from dataclasses import dataclass, field
from decimal import Decimal

from .discounts import apply_coupon, volume_discount
from .money import to_money
from .tax import tax_for


@dataclass
class Line:
    description: str
    quantity: int
    unit_price: Decimal
    category: str = "standard"

    @property
    def amount(self) -> Decimal:
        return to_money(self.unit_price * self.quantity)


@dataclass
class Invoice:
    number: str
    lines: list[Line] = field(default_factory=list)
    coupon: str | None = None

    def add(self, line: Line) -> None:
        if line.quantity <= 0:
            raise ValueError("quantity must be positive")
        self.lines.append(line)

    def subtotal(self) -> Decimal:
        return sum((line.amount for line in self.lines), Decimal("0.00"))

    def discount(self, coupons: dict[str, Decimal]) -> Decimal:
        sub = self.subtotal()
        return volume_discount(sub) + apply_coupon(sub, self.coupon, coupons)

    def tax(self, coupons: dict[str, Decimal]) -> Decimal:
        """Tax is charged on each line after its share of the discount."""
        sub = self.subtotal()
        if sub == 0:
            return Decimal("0.00")
        ratio = (sub - self.discount(coupons)) / sub
        return sum((tax_for(line.amount * ratio, line.category) for line in self.lines), Decimal("0.00"))

    def total(self, coupons: dict[str, Decimal]) -> Decimal:
        return self.subtotal() - self.discount(coupons) + self.tax(coupons)
