from decimal import Decimal

from .money import to_money

RATES = {"standard": Decimal("0.18"), "reduced": Decimal("0.05"), "exempt": Decimal("0")}


def tax_for(amount: Decimal, category: str = "standard") -> Decimal:
    """Tax on a line amount, rounded to cents. Unknown categories raise KeyError."""
    return to_money(amount * RATES[category])


def split_gst(tax: Decimal, interstate: bool) -> dict[str, Decimal]:
    """Interstate supply pays IGST; within a state, CGST and SGST split the tax equally."""
    if interstate:
        return {"igst": tax}
    half = to_money(tax / 2)
    return {"cgst": half, "sgst": tax - half}
