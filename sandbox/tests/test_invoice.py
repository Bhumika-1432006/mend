from decimal import Decimal

import pytest

from invoicer.invoice import Invoice, Line

COUPONS = {"WELCOME": Decimal("100")}


def make():
    inv = Invoice("INV-1")
    inv.add(Line("Widget", 2, Decimal("1500.00")))
    inv.add(Line("Manual", 1, Decimal("2000.00"), "reduced"))
    return inv


def test_line_amount():
    assert Line("x", 3, Decimal("19.99")).amount == Decimal("59.97")


def test_subtotal_and_volume_discount():
    inv = make()
    assert inv.subtotal() == Decimal("5000.00")
    assert inv.discount(COUPONS) == Decimal("250.00")


def test_tax_after_discount():
    inv = make()
    # 95% of each line is taxed: 3000*0.95*0.18 + 2000*0.95*0.05
    assert inv.tax(COUPONS) == Decimal("608.00")
    assert inv.total(COUPONS) == Decimal("5358.00")


def test_coupon_stacks_with_volume_discount():
    inv = make()
    inv.coupon = "welcome"
    assert inv.discount(COUPONS) == Decimal("350.00")


def test_empty_invoice_totals_zero():
    assert Invoice("INV-0").total(COUPONS) == Decimal("0.00")


def test_invoices_do_not_share_lines():
    a, b = Invoice("A"), Invoice("B")
    a.add(Line("x", 1, Decimal("1")))
    assert b.lines == []


def test_rejects_non_positive_quantity():
    with pytest.raises(ValueError):
        Invoice("X").add(Line("x", 0, Decimal("1")))
