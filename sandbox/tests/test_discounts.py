from decimal import Decimal

from invoicer.discounts import apply_coupon, volume_discount

COUPONS = {"WELCOME": Decimal("100"), "BIG": Decimal("5000")}


def test_volume_discount_tiers():
    assert volume_discount(Decimal("4999.99")) == Decimal("0.00")
    assert volume_discount(Decimal("5000.00")) == Decimal("250.00")
    assert volume_discount(Decimal("10000.00")) == Decimal("1000.00")
    assert volume_discount(Decimal("20000.00")) == Decimal("2000.00")


def test_coupon_is_case_insensitive_and_trimmed():
    assert apply_coupon(Decimal("500"), " welcome ", COUPONS) == Decimal("100.00")


def test_coupon_capped_at_subtotal():
    assert apply_coupon(Decimal("300"), "BIG", COUPONS) == Decimal("300")


def test_no_or_unknown_coupon():
    assert apply_coupon(Decimal("300"), None, COUPONS) == Decimal("0.00")
    assert apply_coupon(Decimal("300"), "NOPE", COUPONS) == Decimal("0.00")
