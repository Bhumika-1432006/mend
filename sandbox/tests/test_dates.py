from datetime import date

import pytest

from invoicer.dates import add_business_days, due_date, is_overdue


def test_add_business_days_skips_weekend():
    friday = date(2026, 10, 9)
    assert add_business_days(friday, 1) == date(2026, 10, 12)
    assert add_business_days(friday, 5) == date(2026, 10, 16)


def test_add_zero_business_days_is_same_day():
    assert add_business_days(date(2026, 10, 10), 0) == date(2026, 10, 10)


def test_due_date_net_and_eom():
    assert due_date(date(2026, 1, 31), "NET 30") == date(2026, 3, 2)
    assert due_date(date(2026, 2, 10), "eom") == date(2026, 2, 28)
    assert due_date(date(2026, 12, 5), " EOM ") == date(2026, 12, 31)


def test_due_date_unknown_terms():
    with pytest.raises(ValueError):
        due_date(date(2026, 1, 1), "NET")


def test_overdue_starts_the_day_after_due():
    due = date(2026, 10, 10)
    assert not is_overdue(due, date(2026, 10, 10))
    assert is_overdue(due, date(2026, 10, 11))
