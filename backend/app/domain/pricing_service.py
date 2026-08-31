from .catalog import PRODUCTS
from .business_config import SALES_POLICY


class PricingService:
    def get_unit_price(self, product_id: str, customer_type: str = "REGULAR") -> float:
        product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if not product:
            raise ValueError("PRODUCT_NOT_FOUND")
        if customer_type.upper() == "MEMBER":
            return round(product["price"] * SALES_POLICY["member_discount_rate"], 2)
        return product["price"]

    def calculate_order_quote(self, items: list[dict], discount: float = 0, shipping: float | None = None, customer_type: str = "REGULAR", delivery_mode: str = "PICKUP") -> dict:
        lines = []
        regular_subtotal = 0
        for item in items:
            product = next((p for p in PRODUCTS if p["id"] == item.get("product_id")), None)
            if not product:
                return {"ok": False, "reason": "PRODUCT_NOT_FOUND"}
            quantity = int(item.get("quantity", 1))
            if quantity < 1:
                return {"ok": False, "reason": "INVALID_QUANTITY"}
            regular_line = product["price"] * quantity
            unit_price = self.get_unit_price(product["id"], customer_type)
            lines.append({"product_id": product["id"], "name": product["name"], "quantity": quantity, "unit_price": unit_price, "subtotal": round(unit_price * quantity, 2)})
            regular_subtotal += regular_line
        subtotal = round(sum(line["subtotal"] for line in lines), 2)
        member_discount = round(regular_subtotal - subtotal, 2) if customer_type.upper() == "MEMBER" else 0
        threshold_discount = max((float(rule["discount"]) for rule in SALES_POLICY["threshold_discounts"] if regular_subtotal >= float(rule["threshold"])), default=0)
        manual_discount = max(float(discount), 0)
        discount = round(member_discount + threshold_discount + manual_discount, 2)
        delivery_mode = (delivery_mode or SALES_POLICY.get("default_delivery_mode", "PICKUP")).upper()
        if delivery_mode not in {"PICKUP", "SHIPPING"}:
            return {"ok": False, "reason": "INVALID_DELIVERY_MODE"}
        shipping_subsidy = 0
        if shipping is None:
            if delivery_mode == "PICKUP":
                shipping = 0
            elif regular_subtotal >= float(SALES_POLICY["free_shipping_threshold"]):
                shipping = 0
            elif regular_subtotal >= float(SALES_POLICY.get("shipping_subsidy_threshold", 50)):
                rate = float(SALES_POLICY.get("shipping_subsidy_rate", 0))
                base_shipping = float(SALES_POLICY["shipping_fee"])
                shipping_subsidy = round(base_shipping * rate, 2)
                shipping = round(base_shipping - shipping_subsidy, 2)
            else:
                shipping = float(SALES_POLICY["shipping_fee"])
        shipping = max(float(shipping), 0)
        next_rules = sorted((rule for rule in SALES_POLICY["threshold_discounts"] if regular_subtotal < float(rule["threshold"])), key=lambda rule: float(rule["threshold"]))
        next_promotion = None
        if next_rules:
            rule = next_rules[0]
            next_promotion = {"label": rule.get("label", f"满{rule['threshold']}减{rule['discount']}"), "threshold": rule["threshold"], "remaining": round(float(rule["threshold"]) - regular_subtotal, 2), "message": f"再加购约{round(float(rule['threshold']) - regular_subtotal, 2)}元商品，即可享受{rule.get('label', '')}。"}
        if delivery_mode == "SHIPPING" and regular_subtotal < float(SALES_POLICY["free_shipping_threshold"]):
            remaining = round(float(SALES_POLICY["free_shipping_threshold"]) - regular_subtotal, 2)
            if not next_promotion or remaining < next_promotion["remaining"]:
                next_promotion = {"label": "满80元包邮", "threshold": SALES_POLICY["free_shipping_threshold"], "remaining": remaining, "message": f"再加购约{remaining}元商品即可享受满80元包邮。"}
        return {"ok": True, "data": {"items": lines, "subtotal": subtotal, "regular_subtotal": regular_subtotal, "discount": discount, "discount_breakdown": {"member": member_discount, "threshold": threshold_discount, "manual": manual_discount}, "shipping": shipping, "shipping_subsidy": shipping_subsidy, "delivery_mode": delivery_mode, "free_shipping": delivery_mode == "SHIPPING" and shipping == 0, "total": round(subtotal - threshold_discount - manual_discount + shipping, 2), "next_promotion": next_promotion}}


_SERVICE = PricingService()


def calculate_total(items: list[dict]) -> dict:
    quote = _SERVICE.calculate_order_quote(items)
    if quote["ok"]:
        quote["data"].pop("discount", None)
        quote["data"].pop("shipping", None)
    return quote


def calculate_order_quote(items: list[dict], discount: float = 0, shipping: float | None = None, customer_type: str = "REGULAR", delivery_mode: str = "PICKUP") -> dict:
    return _SERVICE.calculate_order_quote(items, discount, shipping, customer_type, delivery_mode)
