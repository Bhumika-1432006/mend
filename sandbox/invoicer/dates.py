from datetime import date, timedelta


def add_business_days(start: date, days: int) -> date:
    """Move forward `days` business days (Mon-Fri), skipping weekends."""
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def due_date(issued: date, terms: str) -> date:
    """Terms are "NET <n>" (calendar days) or "EOM" (last day of the issue month)."""
    terms = terms.strip().upper()
    if terms == "EOM":
        next_month = issued.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)
    if terms.startswith("NET "):
        return issued + timedelta(days=int(terms[4:]))
    raise ValueError(f"unknown terms: {terms}")


def is_overdue(due: date, today: date) -> bool:
    """An invoice is overdue the day after its due date."""
    return today > due
