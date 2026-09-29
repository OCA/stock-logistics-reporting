# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

import pytz
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang

if TYPE_CHECKING:
    from odoo.api import Environment


WEEKDAY_NUMBER = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_SHORT_DATE_UNIT = {
    "d": "days",
    "w": "weeks",
    "m": "months",
    "y": "years",
    "H": "hours",
    "M": "minutes",
    "S": "seconds",
}

TRUNCATE_TODAY = relativedelta(hour=0, minute=0, second=0, microsecond=0)
TRUNCATE_UNIT = {
    "year": relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
    "month": relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0),
    "day": relativedelta(hour=0, minute=0, second=0, microsecond=0),
    "hour": relativedelta(minute=0, second=0, microsecond=0),
    "minute": relativedelta(second=0, microsecond=0),
    "second": relativedelta(microsecond=0),
}


def parse_iso_date(value: str) -> date | datetime:
    value = value.strip()
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        if "T" in normalized or " " in normalized:
            return datetime.fromisoformat(normalized)
        return date.fromisoformat(normalized)
    except ValueError as e:
        raise ValueError(f"Invalid term {value!r} in expression date: {value!r}") from e


def parse_date(value: str, env: Environment, naive: bool = True) -> date | datetime:
    # Backport from Odoo 19.0: this method only exists there and is missing in 17.0.
    r"""Parse a technical date string into a date or datetime.

    This supports ISO formatted dates and dates relative to now.
    ``parse_iso_date`` is used if the input starts with ``r'\d+-'``.
    Otherwise, the date is computed by starting from now at user's timezone.
    We can also start ``today`` (resulting in a date type). Then we apply offsets.
    """
    if re.match(r"\d+-", value):
        return parse_iso_date(value)
    terms = value.split()
    if not terms:
        raise ValueError("Empty date value")

    dt: datetime | date = fields.Datetime.now()
    term = terms.pop(0) if terms[0] in ("today", "now") else "now"
    if term == "today":
        dt = fields.Date.context_today(env["base"], dt)
    else:
        dt = fields.Datetime.context_timestamp(env["base"], dt)

    for term in terms:
        operator = term[0]
        if operator not in ("+", "-", "=") or len(term) < 3:
            raise ValueError(f"Invalid term {term!r} in expression date: {value!r}")

        # Weekday
        dayname = term[1:].lower()
        if dayname in WEEKDAY_NUMBER or dayname == "week_start":
            week_start = int(get_lang(env).week_start) - 1
            weekday = week_start if dayname == "week_start" else WEEKDAY_NUMBER[dayname]
            weekday_offset = ((weekday - week_start) % 7) - (
                (dt.weekday() - week_start) % 7
            )
            if operator in ("+", "-"):
                if operator == "+" and weekday_offset < 0:
                    weekday_offset += 7
                elif operator == "-" and weekday_offset > 0:
                    weekday_offset -= 7
            elif isinstance(dt, datetime):
                dt += TRUNCATE_TODAY
            dt += timedelta(weekday_offset)
            continue

        # Operations on dates
        try:
            unit = _SHORT_DATE_UNIT[term[-1]]
            if operator in ("+", "-"):
                number = int(term[:-1])  # positive or negative
            else:
                number = int(term[1:-1])
                unit = unit.removesuffix("s")
                if isinstance(dt, datetime):
                    dt += TRUNCATE_UNIT[unit]
                # note: '=Nw' is not supported
            dt += relativedelta(**{unit: number})
        except (ValueError, TypeError, KeyError) as e:
            raise ValueError(
                f"Invalid term {term!r} in expression date: {value!r}"
            ) from e

    # always return a naive date
    if naive and isinstance(dt, datetime) and dt.tzinfo is not None:
        dt = dt.astimezone(pytz.utc).replace(tzinfo=None)
    return dt


class ProductDemandPeriod(models.Model):
    _name = "product.demand.period"
    _description = "Product demand period"
    _order = "sequence, id"
    _rec_name = "name"

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    name = fields.Char(required=True, translate=True)
    start_expression = fields.Char(
        required=True,
        help="Start of the time window used to search for outgoing stock moves. "
        "Use 'today' or 'now' followed by optional offsets: ±Nd (days), ±Nw (weeks), "
        "±Nm (months), ±Ny (years). Use =1d for first day of month, =6m for a given "
        "month.",
    )
    end_expression = fields.Char(
        default="now",
        required=True,
        help="End of the time window used to search for outgoing stock moves (demand). "
        "Same syntax as Start: 'today'/'now' with ±Nd, ±Nw, ±Nm, ±Ny, or =1d, =6m.",
    )

    @api.constrains("start_expression", "end_expression")
    def _check_expressions(self):
        for period in self:
            try:
                start = fields.Datetime.to_datetime(
                    parse_date(period.start_expression, period.env)
                )
                end = fields.Datetime.to_datetime(
                    parse_date(period.end_expression, period.env)
                )
            except ValueError as e:
                raise UserError(
                    _(
                        "Invalid date expression: %(error)s",
                        error=str(e),
                    )
                ) from e
            if start > end:
                raise UserError(
                    _(
                        "Start expression must be before or equal to end expression "
                        'for period "%(name)s".',
                        name=period.name,
                    )
                )

    @api.model
    def _get_demand_period_info_fnames(self) -> list[str]:
        """Fields that will be included in the demand_period_info dict."""
        return ["sequence", "name"]
