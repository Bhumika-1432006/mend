from decimal import Decimal

import pytest

from invoicer.tax import split_gst, tax_for


def test_tax_rates():
    assert tax_for(Decimal("100.00")) == Decimal("18.00")
    assert tax_for(Decimal("100.00"), "reduced") == Decimal("5.00")
    assert tax_for(Decimal("100.00"), "exempt") == Decimal("0.00")


def test_tax_rounds_to_cents():
    assert tax_for(Decimal("0.25")) == Decimal("0.05")


def test_unknown_category_raises():
    with pytest.raises(KeyError):
        tax_for(Decimal("1"), "luxury")


def test_split_gst_intrastate_adds_up():
    parts = split_gst(Decimal("18.01"), interstate=False)
    assert parts == {"cgst": Decimal("9.01"), "sgst": Decimal("9.00")}


def test_split_gst_interstate():
    assert split_gst(Decimal("18.00"), interstate=True) == {"igst": Decimal("18.00")}
