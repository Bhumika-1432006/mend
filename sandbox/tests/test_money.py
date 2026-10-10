from decimal import Decimal

import pytest

from invoicer.money import format_money, split_evenly, to_money


def test_to_money_parses_strings_with_commas():
    assert to_money("1,234.50") == Decimal("1234.50")


def test_to_money_rounds_half_up():
    assert to_money("2.675") == Decimal("2.68")
    assert to_money(0.125) == Decimal("0.13")


def test_format_money():
    assert format_money(Decimal("1234.5")) == "INR 1,234.50"
    assert format_money(Decimal("-12"), "USD") == "-USD 12.00"


def test_split_evenly_adds_up_and_front_loads_cents():
    assert split_evenly(Decimal("10.00"), 3) == [Decimal("3.34"), Decimal("3.33"), Decimal("3.33")]
    assert sum(split_evenly(Decimal("100.01"), 7)) == Decimal("100.01")


def test_split_evenly_rejects_zero_parts():
    with pytest.raises(ValueError):
        split_evenly(Decimal("1"), 0)
