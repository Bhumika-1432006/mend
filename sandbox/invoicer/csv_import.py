import csv
import io
from decimal import Decimal

from .invoice import Invoice, Line
from .money import to_money

REQUIRED = ("invoice", "description", "quantity", "unit_price")


def parse_invoices(text: str) -> dict[str, Invoice]:
    """Parse CSV rows into invoices keyed by invoice number, keeping row order.

    Columns: invoice, description, quantity, unit_price, category (optional, default standard).
    Header names are case-insensitive and may have spaces around them. Blank lines are skipped.
    """
    reader = csv.DictReader(io.StringIO(text))
    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames or []]
    missing = [col for col in REQUIRED if col not in reader.fieldnames]
    if missing:
        raise ValueError(f"missing columns: {', '.join(missing)}")
    invoices: dict[str, Invoice] = {}
    for row in reader:
        if not any((v or "").strip() for v in row.values()):
            continue
        number = row["invoice"].strip()
        inv = invoices.setdefault(number, Invoice(number))
        inv.add(Line(
            description=row["description"].strip(),
            quantity=int(row["quantity"]),
            unit_price=to_money(row["unit_price"]),
            category=(row.get("category") or "standard").strip().lower() or "standard",
        ))
    return invoices
