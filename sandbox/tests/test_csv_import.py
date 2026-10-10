from decimal import Decimal

import pytest

from invoicer.csv_import import parse_invoices

CSV = """Invoice , Description, Quantity ,Unit_Price,Category
INV-1, Widget ,2,"1,500.00",
INV-2,Manual,1,200.00,Reduced

INV-1,Cable,3,10.50,standard
"""


def test_groups_rows_by_invoice_in_order():
    invoices = parse_invoices(CSV)
    assert list(invoices) == ["INV-1", "INV-2"]
    assert [l.description for l in invoices["INV-1"].lines] == ["Widget", "Cable"]


def test_parses_amounts_and_categories():
    invoices = parse_invoices(CSV)
    widget = invoices["INV-1"].lines[0]
    assert widget.unit_price == Decimal("1500.00")
    assert widget.category == "standard"
    assert invoices["INV-2"].lines[0].category == "reduced"


def test_missing_column_is_reported():
    with pytest.raises(ValueError, match="unit_price"):
        parse_invoices("invoice,description,quantity\nA,x,1\n")
