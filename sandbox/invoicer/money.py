from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def to_money(value) -> Decimal:
    """Parse a number or string like "1,234.50" into a Decimal rounded to cents."""
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def format_money(amount: Decimal, currency: str = "INR") -> str:
    """Format like "INR 1,234.50"; negative amounts as "-INR 12.00"."""
    sign = "-" if amount < 0 else ""
    return f"{sign}{currency} {abs(amount):,.2f}"


def split_evenly(total: Decimal, parts: int) -> list[Decimal]:
    """Split a total into `parts` cent amounts that add up exactly; earlier parts get the extra cents."""
    if parts <= 0:
        raise ValueError("parts must be positive")
    cents = int((total / CENT).to_integral_value())
    base, extra = divmod(cents, parts)
    return [(Decimal(base + (1 if i < extra else 0)) * CENT) for i in range(parts)]
