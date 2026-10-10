from datetime import date
from decimal import Decimal

import pytest

from invoicer.ledger import Ledger


def make():
    led = Ledger()
    led.invoice("Acme", "INV-1", "1000.00", date(2026, 7, 1), date(2026, 7, 31))
    led.invoice("Acme", "INV-2", "500.00", date(2026, 8, 1), date(2026, 8, 31))
    led.payment("Acme", "PAY-1", "1200.00", date(2026, 8, 15))
    led.invoice("Beta", "INV-9", "300.00", date(2026, 9, 1), date(2026, 9, 15))
    return led


def test_balances_and_receivable():
    led = make()
    assert led.balance("Acme") == Decimal("300.00")
    assert led.balance("Acme", as_of=date(2026, 8, 1)) == Decimal("1500.00")
    led.payment("Beta", "PAY-2", "400.00", date(2026, 9, 20))
    assert led.balance("Beta") == Decimal("-100.00")
    assert led.total_receivable() == Decimal("300.00")


def test_post_validation():
    led = make()
    with pytest.raises(ValueError):
        led.invoice("Acme", "INV-1", "10", date(2026, 9, 1), date(2026, 9, 2))
    with pytest.raises(ValueError):
        led.post("Acme", "invoice", "INV-3", "10", date(2026, 9, 1))
    with pytest.raises(ValueError):
        led.payment("Acme", "PAY-9", "0", date(2026, 9, 1))


def test_payments_settle_oldest_invoice_first():
    items = {i.reference: i for i in make().open_items("Acme")}
    assert items["INV-1"].remaining == Decimal("0.00")
    assert items["INV-2"].remaining == Decimal("300.00")


def test_unallocated_credit():
    led = make()
    led.credit("Acme", "CN-1", "400.00", date(2026, 9, 1))
    assert led.unallocated_credit("Acme") == Decimal("100.00")


def test_aging_buckets_and_boundaries():
    led = make()
    assert led.aging("Acme", date(2026, 8, 31))["current"] == Decimal("300.00")
    assert led.aging("Acme", date(2026, 9, 30))["1-30"] == Decimal("300.00")   # day 30
    assert led.aging("Acme", date(2026, 10, 1))["31-60"] == Decimal("300.00")  # day 31
    assert led.aging("Acme", date(2026, 12, 15))["90+"] == Decimal("300.00")


def test_late_interest_simple_365():
    led = make()
    # 300.00 * 0.18 * 30 / 365 = 4.438... -> 4.44
    assert led.late_interest("Acme", date(2026, 9, 30)) == Decimal("4.44")
    assert led.late_interest("Acme", date(2026, 8, 31)) == Decimal("0.00")


def test_statement_lines_and_running_balance():
    text = make().statement("Acme")
    lines = text.splitlines()
    assert lines[0] == "Statement for Acme"
    assert "INR 1,500.00" in lines[2]
    assert "-INR 1,200.00" in lines[3]
    assert lines[-1] == "Balance due: INR 300.00"


def test_export_rows():
    rows = make().export_rows()
    assert rows[0] == {"customer": "Acme", "kind": "invoice", "reference": "INV-1",
                       "amount": "1000.00", "date": "2026-07-01", "due": "2026-07-31"}
    assert rows[2]["due"] == ""
