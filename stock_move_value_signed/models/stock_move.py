# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    value_signed = fields.Monetary(
        string="Signed Value",
        currency_field="company_currency_id",
        compute="_compute_value_signed",
        store=True,
        help="Value of the move, positive when it enters the company stock "
        "and negative when it leaves it.",
    )

    @api.depends("value", "is_in", "is_out")
    def _compute_value_signed(self):
        for move in self:
            if move.is_in:
                move.value_signed = move.value
            elif move.is_out:
                move.value_signed = -move.value
            else:
                move.value_signed = 0.0
