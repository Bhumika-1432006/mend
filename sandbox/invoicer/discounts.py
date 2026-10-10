from decimal import Decimal

from .money import to_money

# (minimum subtotal, percent off), checked from the highest threshold down
VOLUME_TIERS = [(Decimal("10000"), Decimal("10")), (Decimal("5000"), Decimal("5"))]


def volume_discount(subtotal: Decimal) -> Decimal:
    """Discount amount for a subtotal; a subtotal exactly at a threshold qualifies."""
    for threshold, percent in VOLUME_TIERS:
        if subtotal >= threshold:
            return to_money(subtotal * percent / 100)
    return Decimal("0.00")


def apply_coupon(subtotal: Decimal, code: str | None, coupons: dict[str, Decimal]) -> Decimal:
    """Flat coupon amount, never more than the subtotal. Codes are case-insensitive."""
    if not code:
        return Decimal("0.00")
    amount = coupons.get(code.strip().upper(), Decimal("0"))
    return min(to_money(amount), subtotal)
