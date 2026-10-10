"""Customer ledger: invoices, payments, credit notes, allocation, aging, interest, statements.

This module is intentionally longer than one default read_file page (200 lines).
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from .dates import is_overdue
from .money import CENT, format_money, to_money

# ---------------------------------------------------------------------------
# Entries
# ---------------------------------------------------------------------------

INVOICE = "invoice"
PAYMENT = "payment"
CREDIT = "credit"
KINDS = (INVOICE, PAYMENT, CREDIT)


@dataclass
class Entry:
    """One ledger entry. Invoices increase what the customer owes; payments and credits reduce it."""

    customer: str
    kind: str
    reference: str
    amount: Decimal
    on: date
    due: date | None = None

    def signed(self) -> Decimal:
        """Positive for invoices, negative for payments and credit notes."""
        return self.amount if self.kind == INVOICE else -self.amount


@dataclass
class OpenItem:
    """An invoice with what is still unpaid on it."""

    reference: str
    issued: date
    due: date
    original: Decimal
    remaining: Decimal

    @property
    def settled(self) -> bool:
        return self.remaining == 0


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _check_kind(kind: str) -> None:
    if kind not in KINDS:
        raise ValueError(f"unknown entry kind: {kind}")


def _check_amount(amount: Decimal) -> Decimal:
    amount = to_money(amount)
    if amount <= 0:
        raise ValueError("amount must be positive")
    return amount


def _check_customer(customer: str) -> str:
    customer = customer.strip()
    if not customer:
        raise ValueError("customer is required")
    return customer


# ---------------------------------------------------------------------------
# The ledger
# ---------------------------------------------------------------------------


@dataclass
class Ledger:
    entries: list[Entry] = field(default_factory=list)

    # -- posting -------------------------------------------------------------

    def post(self, customer: str, kind: str, reference: str, amount, on: date, due: date | None = None) -> Entry:
        """Record an entry. Invoices need a due date; references must be unique per customer."""
        _check_kind(kind)
        customer = _check_customer(customer)
        amount = _check_amount(amount)
        if kind == INVOICE and due is None:
            raise ValueError("invoices need a due date")
        if any(e.customer == customer and e.reference == reference for e in self.entries):
            raise ValueError(f"duplicate reference {reference} for {customer}")
        entry = Entry(customer, kind, reference, amount, on, due)
        self.entries.append(entry)
        return entry

    def invoice(self, customer: str, reference: str, amount, on: date, due: date) -> Entry:
        return self.post(customer, INVOICE, reference, amount, on, due)

    def payment(self, customer: str, reference: str, amount, on: date) -> Entry:
        return self.post(customer, PAYMENT, reference, amount, on)

    def credit(self, customer: str, reference: str, amount, on: date) -> Entry:
        return self.post(customer, CREDIT, reference, amount, on)

    # -- queries ---------------------------------------------------------------

    def customers(self) -> list[str]:
        """Customers in the order they first appear."""
        seen: list[str] = []
        for e in self.entries:
            if e.customer not in seen:
                seen.append(e.customer)
        return seen

    def entries_for(self, customer: str) -> list[Entry]:
        """A customer's entries in date order; same-day entries keep posting order."""
        mine = [e for e in self.entries if e.customer == customer]
        return sorted(mine, key=lambda e: e.on)

    def balance(self, customer: str, as_of: date | None = None) -> Decimal:
        """What the customer owes (negative means we owe them), counting entries up to `as_of`."""
        total = Decimal("0.00")
        for e in self.entries_for(customer):
            if as_of is None or e.on <= as_of:
                total += e.signed()
        return total

    def total_receivable(self) -> Decimal:
        """Sum of positive balances only; customers in credit are not netted against debtors."""
        return sum((b for b in (self.balance(c) for c in self.customers()) if b > 0), Decimal("0.00"))

    # -- allocation --------------------------------------------------------------

    def open_items(self, customer: str) -> list[OpenItem]:
        """Invoices with their unpaid amounts after allocating payments and credits.

        Payments and credit notes settle the OLDEST invoice first (FIFO by issue date).
        Money left over after every invoice is settled stays as an unallocated credit.
        """
        items = [
            OpenItem(e.reference, e.on, e.due, e.amount, e.amount)
            for e in self.entries_for(customer)
            if e.kind == INVOICE
        ]
        pool = sum((e.amount for e in self.entries_for(customer) if e.kind != INVOICE), Decimal("0.00"))
        for item in sorted(items, key=lambda i: i.issued):
            if pool <= 0:
                break
            applied = min(pool, item.remaining)
            item.remaining -= applied
            pool -= applied
        return items

    def unallocated_credit(self, customer: str) -> Decimal:
        """Payments and credits not used up by invoices."""
        paid = sum((e.amount for e in self.entries_for(customer) if e.kind != INVOICE), Decimal("0.00"))
        billed = sum((e.amount for e in self.entries_for(customer) if e.kind == INVOICE), Decimal("0.00"))
        return max(paid - billed, Decimal("0.00"))

    # -- aging -----------------------------------------------------------------

    def aging(self, customer: str, today: date) -> dict[str, Decimal]:
        """Unpaid amounts by days past due.

        Buckets: "current" (not yet overdue), "1-30", "31-60", "61-90", "90+".
        An invoice is in "1-30" from the first overdue day through day 30.
        """
        buckets = {name: Decimal("0.00") for name in ("current", "1-30", "31-60", "61-90", "90+")}
        for item in self.open_items(customer):
            if item.settled:
                continue
            if not is_overdue(item.due, today):
                buckets["current"] += item.remaining
                continue
            days = (today - item.due).days
            if days <= 30:
                buckets["1-30"] += item.remaining
            elif days <= 60:
                buckets["31-60"] += item.remaining
            elif days <= 90:
                buckets["61-90"] += item.remaining
            else:
                buckets["90+"] += item.remaining
        return buckets

    # -- interest ----------------------------------------------------------------

    def late_interest(self, customer: str, today: date, annual_rate: Decimal = Decimal("0.18")) -> Decimal:
        """Simple interest on overdue unpaid amounts, on a 365-day year, rounded per invoice."""
        total = Decimal("0.00")
        for item in self.open_items(customer):
            if item.settled or not is_overdue(item.due, today):
                continue
            days = (today - item.due).days
            total += to_money(item.remaining * annual_rate * days / 365)
        return total

    # -- statements ------------------------------------------------------------

    def statement(self, customer: str, currency: str = "INR") -> str:
        """Plain-text statement: one line per entry with a running balance, then the total."""
        lines = [f"Statement for {customer}"]
        running = Decimal("0.00")
        for e in self.entries_for(customer):
            running += e.signed()
            lines.append(
                f"{e.on.isoformat()}  {e.kind:<8} {e.reference:<10} "
                f"{format_money(e.signed(), currency):>16}  {format_money(running, currency):>16}"
            )
        lines.append(f"Balance due: {format_money(running, currency)}")
        return "\n".join(lines)

    # -- export ------------------------------------------------------------------

    def export_rows(self) -> list[dict[str, str]]:
        """Entries as flat string rows for CSV export, in posting order."""
        rows = []
        for e in self.entries:
            rows.append({
                "customer": e.customer,
                "kind": e.kind,
                "reference": e.reference,
                "amount": f"{e.amount.quantize(CENT)}",
                "date": e.on.isoformat(),
                "due": e.due.isoformat() if e.due else "",
            })
        return rows
