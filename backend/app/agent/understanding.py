import asyncio
import json
import os
import re
import threading

from .contracts import ProductMention, RequestedItem, UnderstandingOutput
from .state import CustomerServiceState, Message
from ..domain.catalog import PRODUCTS
from ..domain.media_service import resolve_alias
from ..llm import get_provider
from .intent_canonicalizer import canonicalize_understanding

def normalize_message(text: str) -> str:
    return " ".join(text.split())

def extract_known_facts(text: str) -> dict:
    facts = {}
    if "昨天" in text:
        facts["purchase_time"] = "昨天"
    if "低糖" in text:
        facts["preference"] = "低糖"
    return facts


def _delivery_slot_values(text: str) -> dict:
    """Extract delivery slots generically before planning; never invent values."""
    slots: dict[str, str] = {}
    phone = re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)", text)
    if phone:
        slots["phone"] = phone.group(0)
    name = re.search(r"(?:收货人|联系人|姓名)\s*[:：]?\s*([\u4e00-\u9fa5]{2,4})", text)
    if name:
        slots["recipient_name"] = name.group(1)
    address_like = any(token in text for token in ("省", "市", "区", "县", "镇", "乡", "街道", "路", "花园", "号", "栋", "室"))
    if address_like and len(re.sub(r"[，,。；;\s]", "", text)) >= 8:
        slots["delivery_address"] = text.strip(" ，,。；;")
    return slots

def _run(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    result = []
    thread = threading.Thread(target=lambda: result.append(asyncio.run(coro)))
    thread.start()
    thread.join()
    return result[0]

def _quantity_before(text: str, start: int) -> int:
    numbers = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    match = re.search(r"(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个?\s*$", text[max(0, start - 8):start])
    if not match:
        after = re.search(r"(?:改成|调整为|变成)\s*(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个?", text[start:start + 16])
        if after:
            return int(after.group(1)) if after.group(1).isdigit() else numbers[after.group(1)]
        return 1
    return int(match.group(1)) if match.group(1).isdigit() else numbers[match.group(1)]


def _quantity_for_product(text: str, product_name: str, default: int = 1) -> int:
    numbers = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    if default != 1:
        return default
    match = re.search(re.escape(product_name) + r"\s*[，,：:]?\s*[（(]?\s*(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个", text)
    if not match:
        match = re.search(re.escape(product_name) + r".{0,8}?(?:买|要|来|留)\s*(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*(?:份|个)", text)
    if not match:
        return default
    raw = match.group(1)
    return int(raw) if raw.isdigit() else numbers[raw]


def _operation(text: str) -> str:
    if any(word in text for word in ("不要", "去掉", "删掉", "取消")):
        return "REMOVE"
    if any(word in text for word in ("改成", "调整为", "变成")):
        return "SET_QUANTITY"
    if any(word in text for word in ("换成", "换为")):
        return "REPLACE"
    if any(word in text for word in ("继续", "保留")):
        return "KEEP"
    return "ADD"


def _deterministic_understanding(text: str) -> UnderstandingOutput:
    """Offline safety parser; production semantics come from the LLM contract."""
    mentions = []
    requested = []
    operation = _operation(text)
    for product in sorted(PRODUCTS, key=lambda item: len(item["name"]), reverse=True):
        start = text.find(product["name"])
        if start < 0:
            continue
        quantity = _quantity_for_product(text, product["name"], _quantity_before(text, start))
        mentions.append(ProductMention(text=product["name"], product_query=product["name"]))
        requested.append(RequestedItem(query=product["name"], quantity=quantity, operation=operation, category=product.get("category")))
    # A category-level mutation (e.g. “贝果改成三个”) is a semantic request,
    # not a missing product name. Keep the category as the resolver input and
    # let the state layer decide which selected items it can safely mutate.
    if not requested and operation == "SET_QUANTITY":
        for category in sorted({product.get("category") for product in PRODUCTS if product.get("category")}, key=len, reverse=True):
            if category in text:
                quantity_match = re.search(r"(?:改成|调整为|变成)\s*(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个?", text)
                if quantity_match:
                    raw = quantity_match.group(1)
                    quantity = int(raw) if raw.isdigit() else {"一":1,"两":2,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10}[raw]
                    requested.append(RequestedItem(query=category, quantity=quantity, operation="SET_QUANTITY", category=category))
                break
    price_request = any(word in text for word in ("多少钱", "多收钱", "合计", "总价", "一起要", "一共多少", "算一下", "算算"))
    inventory_request = any(word in text for word in ("有货", "库存", "还有", "可以买", "能买", "吗", "么"))
    purchase_request = bool(requested) and not any(word in text for word in ("不要", "去掉", "删掉", "取消")) and any(word in text for word in ("要", "买", "来", "需要", "给我"))
    goals = []
    explicit_quantity = any(item.quantity > 1 for item in requested)
    browse_request = any(word in text for word in ("有什么", "哪些")) and any(category in text for category in ("贝果", "吐司", "欧包", "盐面包", "小面包"))
    compare_request = any(word in text for word in ("哪个最便宜", "最便宜的是哪个", "哪个便宜", "差多少", "比较一下"))
    recommendation_request = any(word in text for word in ("推荐", "适合", "不喜欢太甜", "热卖", "长辈", "清淡", "送给")) or ("低糖" in text and not requested)
    faq_request = any(word in text for word in ("怎么保存", "如何保存", "怎么加热", "如何加热", "加热", "切片", "预留", "晚点来取", "晚点取", "取货", "吃不完", "放哪里"))
    reservation_request = any(word in text for word in ("帮我留", "帮我预留", "留一个", "留两个", "预留一个", "预留两个")) or ("还有" in text and "要" in text and "个" in text)
    policy_request = "优惠" in text and not requested
    pickup_request = any(word in text for word in ("到店取", "到店拿", "自取", "不需要邮购", "不用邮寄"))
    shipping_request = any(word in text for word in ("包邮", "邮寄", "寄送", "配送", "顺丰")) and not pickup_request
    if "什么时候" in text and any(word in text for word in ("老人", "老人家", "小孩", "小朋友")):
        return UnderstandingOutput(goals=["OTHER"], requires_clarification=True)
    if requested and any(word in text for word in ("适合", "适不适合", "会不会太硬", "会不会太软")):
        audience = "儿童" if any(word in text for word in ("小孩", "小朋友", "孩子")) else "老人" if any(word in text for word in ("老人", "老人家", "长辈")) else None
        constraints = {"audience": audience} if audience else {}
        constraints["concern"] = "texture" if any(word in text for word in ("硬", "软", "口感")) else "audience"
        return UnderstandingOutput(goals=["PRODUCT_FIT_QUERY"], requested_items=requested, product_mentions=mentions, constraints=constraints)
    if reservation_request and requested:
        goals.append("RESERVATION")
    elif faq_request:
        goals.append("FAQ")
    elif compare_request:
        goals.append("PRODUCT_COMPARE")
    elif recommendation_request:
        goals.append("PRODUCT_RECOMMENDATION")
    elif shipping_request:
        goals.append("SHIPPING_POLICY")
    elif "会员" in text and not requested:
        goals.append("MEMBERSHIP_PRICING")
    elif policy_request:
        goals.append("PROMOTION_QUERY")
    elif browse_request:
        goals.append("PRODUCT_BROWSE")
    elif price_request or explicit_quantity:
        goals.append("PRICE_CALCULATION")
    elif purchase_request:
        goals.append("PRICE_CALCULATION")
    if inventory_request:
        goals.append("INVENTORY_CHECK")
    act = "SELECT" if purchase_request else "REQUEST"
    return UnderstandingOutput(goals=goals, requested_items=requested, product_mentions=mentions, conversation_act=act, delivery_intent=shipping_request, delivery_mode="PICKUP" if pickup_request else "SHIPPING" if shipping_request else "UNKNOWN", slot_values=_delivery_slot_values(text))


def resolve_products(understanding: UnderstandingOutput) -> list[dict]:
    """Resolve requested natural-language items to catalog products; never accept an LLM SKU."""
    requested = understanding.requested_items or [RequestedItem(query=item.product_query or item.text) for item in understanding.product_mentions]
    resolved = []
    for item in requested:
        query = item.query.strip()
        alias_product_id = resolve_alias(query)
        if alias_product_id:
            alias_product = next((product for product in PRODUCTS if product["id"] == alias_product_id), None)
            if alias_product:
                resolved.append({"query": query, "product_id": alias_product["id"], "name": alias_product["name"], "quantity": item.quantity, "operation": item.operation, "confidence": 1.0, "match_type": "ALIAS"})
                continue
        exact = [product for product in PRODUCTS if product["name"] == query]
        if exact:
            matches = [(exact[0], 1.0, "EXACT_NAME")]
        else:
            candidates = []
            for product in PRODUCTS:
                haystack = " ".join([product["name"], product.get("category", ""), *product.get("tags", [])])
                score = 0
                if item.category and item.category in haystack:
                    score += 2
                for attribute in item.attributes:
                    if attribute in haystack:
                        score += 2
                if query and query in haystack:
                    score += 3
                if score:
                    candidates.append((product, min(score / 7, 0.99), "ATTRIBUTE_CATEGORY"))
            matches = sorted(candidates, key=lambda value: value[1], reverse=True)
            if matches and len(matches) > 1 and matches[0][1] == matches[1][1]:
                matches = matches[:2]
            else:
                matches = matches[:1]
        if len(matches) == 1:
            product, confidence, match_type = matches[0]
            resolved.append({"query": query, "product_id": product["id"], "name": product["name"], "quantity": item.quantity, "operation": item.operation, "confidence": confidence, "match_type": match_type})
        elif len(matches) > 1:
            resolved.append({"query": query, "candidates": [{"product_id": product["id"], "name": product["name"], "category": product["category"]} for product, _, _ in matches], "quantity": item.quantity, "operation": item.operation})
    return resolved

def understand(state: CustomerServiceState, text: str) -> UnderstandingOutput:
    if os.getenv("LLM_PROVIDER", "mock").lower() == "mock":
        return _deterministic_understanding(text)
    context = {
        "user_message": text,
        "recent_messages": [message.model_dump() for message in state.messages[-6:]],
        "known_facts": state.known_facts,
        "active_goals": state.goals,
        "catalog": [{"id": p["id"], "name": p["name"], "category": p["category"]} for p in PRODUCTS],
    }
    messages = [
        Message(role="system", content="你是 Shanye Shop 的资深智能客服语义理解组件。只输出 JSON，不选择工具，不生成 SKU。输出 goals、requested_items、references、constraints、conversation_operations、semantic_state、constraint_updates、feedback、memory_candidate、conversation_act、slot_values、delivery_intent、delivery_mode。只有客户明确表达长期偏好或明确排除时才输出 memory_candidate；不要把一次购买或模型推断写成长期记忆。delivery_mode 只能是 PICKUP、SHIPPING、UNKNOWN；到店取/自取/不需要邮购表示 PICKUP，邮寄/寄送/配送/顺丰表示 SHIPPING。其余字段按既有格式输出。"),
        Message(role="system", content="Use PRODUCT_FIT_QUERY for product suitability questions and PRODUCT_COMPARE for category cheapest/price comparisons. Set requires_clarification=true for ambiguous time-versus-suitability questions. Normalize CHILD/小孩/小朋友 and SENIOR/老人/老人家 to canonical audience values."),
        Message(role="user", content=json.dumps(context, ensure_ascii=False)),
    ]
    semantic = None
    last_error = None
    for attempt in range(2):
        try:
            semantic = _run(get_provider().structured_generate(messages=messages, output_schema=UnderstandingOutput))
            break
        except Exception as exc:
            last_error = exc
            if attempt == 1:
                # Safe fallback only interprets the current turn. It never
                # creates a SKU from history or executes a historical plan.
                semantic = _deterministic_understanding(text)
    semantic = canonicalize_understanding(semantic)
    known = {item.query for item in semantic.requested_items}
    for product in sorted(PRODUCTS, key=lambda item: len(item["name"]), reverse=True):
        if product["name"] in text and product["name"] not in known:
            semantic.requested_items.append(RequestedItem(query=product["name"], quantity=_quantity_for_product(text, product["name"], _quantity_before(text, text.find(product["name"]))), category=product.get("category")))
    explicit_product = any(product["name"] in text for product in PRODUCTS)
    edit_reference = any(word in text for word in ("再加", "再来", "改成", "换成", "不要", "去掉"))
    explicit_quantity = bool(re.search(r"(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个", text))
    explicit_price = any(word in text for word in ("多少钱", "多收钱", "合计", "总价", "一共", "算一下", "报价"))
    availability_query = explicit_product and any(word in text for word in ("有", "有货", "库存", "还有", "吗", "么")) and not explicit_price
    pickup_request = any(word in text for word in ("到店取", "到店拿", "自取", "不需要邮购", "不用邮寄"))
    if pickup_request:
        semantic.delivery_mode = "PICKUP"
        semantic.delivery_intent = False
        semantic.goals = [goal for goal in semantic.goals if goal != "SHIPPING_POLICY"]
    elif any(word in text for word in ("邮寄", "寄送", "配送", "包邮", "顺丰")):
        semantic.delivery_mode = "SHIPPING"
        semantic.delivery_intent = True
        if "SHIPPING_POLICY" not in semantic.goals:
            semantic.goals.append("SHIPPING_POLICY")
    semantic.slot_values = {**semantic.slot_values, **_delivery_slot_values(text)}
    if explicit_product and any(word in text for word in ("要", "买", "来", "需要")) and not any(word in text for word in ("推荐", "适合", "有什么", "哪些")):
        semantic.conversation_act = "SELECT"
    if availability_query and not edit_reference:
        semantic.goals = [goal for goal in semantic.goals if goal not in {"OTHER", "PRICE_CALCULATION", "PRODUCT_BROWSE"}]
        if "INVENTORY_CHECK" not in semantic.goals:
            semantic.goals.append("INVENTORY_CHECK")
    elif any(word in text for word in ("推荐", "适合", "不喜欢太甜", "热卖", "长辈", "清淡", "送给")):
        semantic.goals = [goal for goal in semantic.goals if goal not in {"OTHER", "INVENTORY_CHECK"}]
        if "PRODUCT_RECOMMENDATION" not in semantic.goals:
            semantic.goals.append("PRODUCT_RECOMMENDATION")
    elif any(word in text for word in ("哪个最便宜", "最便宜的是哪个", "哪个便宜", "差多少", "比较一下")):
        semantic.goals = [goal for goal in semantic.goals if goal not in {"OTHER", "INVENTORY_CHECK"}]
        if "PRODUCT_COMPARE" not in semantic.goals:
            semantic.goals.append("PRODUCT_COMPARE")
    elif explicit_product and (explicit_quantity or any(word in text for word in ("要", "买", "需要", "多少钱", "一共", "合计", "多收钱"))):
        semantic.goals = [goal for goal in semantic.goals if goal not in {"OTHER", "INVENTORY_CHECK", "PRODUCT_BROWSE"}]
        if "PRICE_CALCULATION" not in semantic.goals:
            semantic.goals.append("PRICE_CALCULATION")
    elif "优惠" in text:
        semantic.goals = [goal for goal in semantic.goals if goal != "OTHER"]
        if "PROMOTION_QUERY" not in semantic.goals:
            semantic.goals.append("PROMOTION_QUERY")
    elif "包邮" in text:
        semantic.goals = [goal for goal in semantic.goals if goal != "OTHER"]
        if "SHIPPING_POLICY" not in semantic.goals:
            semantic.goals.append("SHIPPING_POLICY")
    elif "会员" in text:
        semantic.goals = [goal for goal in semantic.goals if goal != "OTHER"]
        if "MEMBERSHIP_PRICING" not in semantic.goals:
            semantic.goals.append("MEMBERSHIP_PRICING")
    elif any(word in text for word in ("怎么保存", "如何保存", "怎么加热", "如何加热", "加热", "切片", "预留", "晚点来取", "晚点取", "取货", "吃不完", "放哪里")):
        semantic.goals = [goal for goal in semantic.goals if goal not in {"OTHER", "INVENTORY_CHECK"}]
        if "FAQ" not in semantic.goals:
            semantic.goals.append("FAQ")
    elif not explicit_product and any(word in text for word in ("有什么", "哪些")) and any(category in text for category in ("贝果", "吐司", "欧包", "盐面包", "小面包")):
        semantic.goals = [goal for goal in semantic.goals if goal not in {"OTHER", "INVENTORY_CHECK"}]
        if "PRODUCT_BROWSE" not in semantic.goals:
            semantic.goals.append("PRODUCT_BROWSE")
    if not explicit_product and not edit_reference and "INVENTORY_CHECK" not in semantic.goals:
        semantic.requested_items = []
        semantic.product_mentions = []
    return semantic
