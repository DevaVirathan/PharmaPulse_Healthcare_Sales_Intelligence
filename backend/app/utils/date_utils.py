"""Date and money helpers."""

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP


def parse_month(value: str) -> tuple[date, date]:
    """Return the first and last day of a YYYY-MM month."""

    try:
        year_str, month_str = value.split("-")
        year, month = int(year_str), int(month_str)
        if month < 1 or month > 12:
            raise ValueError
        start = date(year, month, 1)
    except (ValueError, AttributeError) as exc:
        raise ValueError("month must use YYYY-MM format") from exc
    end = date(year, month, monthrange(year, month)[1])
    return start, end


def previous_month_bounds(start: date) -> tuple[date, date]:
    if start.month == 1:
        prev_year, prev_month = start.year - 1, 12
    else:
        prev_year, prev_month = start.year, start.month - 1
    prev_start = date(prev_year, prev_month, 1)
    prev_end = date(prev_year, prev_month, monthrange(prev_year, prev_month)[1])
    return prev_start, prev_end


def previous_window(start: date, end: date) -> tuple[date, date]:
    """Same-length window immediately before [start, end]."""

    if start > end:
        raise ValueError("start_date must be on or before end_date")
    length = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=length - 1)
    return prev_start, prev_end


def pct_change(current: Decimal, previous: Decimal | None) -> Decimal | None:
    """Percentage change, or None when the baseline is missing or zero.

    The result is rounded half-up to two decimal places so API responses and
    alert explanations are stable and comparable.
    """

    if previous is None or previous == 0:
        return None
    change = (current - previous) / previous * Decimal("100")
    return change.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_inr(value: Decimal) -> str:
    """Format a Decimal as INR using Indian digit grouping."""

    quantized = Decimal(value).quantize(Decimal("0.01"))
    negative = quantized < 0
    text = f"{abs(quantized):.2f}"
    integer_part, decimals = text.split(".")
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        rest = integer_part[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        integer_part = ",".join(groups) + "," + last_three
    sign = "-" if negative else ""
    return f"{sign}₹{integer_part}.{decimals}"
