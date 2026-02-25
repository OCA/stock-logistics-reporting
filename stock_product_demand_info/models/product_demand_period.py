# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.date_utils import parse_date


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
                    period.env._(
                        "Invalid date expression: %(error)s",
                        error=str(e),
                    )
                ) from e
            if start > end:
                raise UserError(
                    period.env._(
                        "Start expression must be before or equal to end expression "
                        'for period "%(name)s".',
                        name=period.name,
                    )
                )

    @api.model
    def _get_demand_period_info_fnames(self) -> list[str]:
        """Fields that will be included in the demand_period_info dict."""
        return ["sequence", "name"]
