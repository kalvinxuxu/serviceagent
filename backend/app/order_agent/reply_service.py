from uuid import uuid4
from .repositories import now
from .trace import record

def compose_reply(draft):
    if not draft.checks: return None
    lines = ["您好，已收到您的订单需求，核验结果如下："]
    for check in draft.checks:
        name = check.get("product_name", "待确认商品")
        if check["fulfillment_status"] == "FULFILLABLE": lines.append(f"- {name}：{check['requested_quantity']:g}个，可满足，单价{check.get('unit_price')}元")
        elif check["fulfillment_status"] == "PARTIAL": lines.append(f"- {name}：需要{check['requested_quantity']:g}个，当前可提供{check['available_quantity']:g}个，缺少{check['requested_quantity']-check['available_quantity']:g}个")
        elif check["fulfillment_status"] == "OUT_OF_STOCK": lines.append(f"- {name}：当前缺货")
        else: lines.append(f"- {name}：暂无法核验，请您确认商品规格")
    if draft.missing_information: lines.append("还请补充：" + "、".join(draft.missing_information))
    lines.append("请确认以上信息后，我们再为您处理订单。")
    draft.reply = {"reply_id": f"rp_{uuid4().hex[:10]}", "draft_id": draft.draft_id, "draft_version": draft.version, "recipient": draft.customer.get("email"), "subject": "订单核验结果", "body": "\n".join(lines), "fact_snapshot": [dict(x) for x in draft.checks], "status": "DRAFT"}
    draft.status = "READY_FOR_CONFIRMATION" if not draft.missing_information and all(x["fulfillment_status"] == "FULFILLABLE" for x in draft.checks) else "CHECKED"
    record(draft.draft_id, "REPLY_DRAFTED", "reply_service", context={"reply_id": draft.reply["reply_id"], "version": draft.version})
    return draft.reply
