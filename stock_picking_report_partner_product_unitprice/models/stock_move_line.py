# Copyright 2026 NICO SOLUTIIONS - ENGERINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_aggregated_properties(self, move_line=None, move=None):
        res = super()._get_aggregated_properties(move_line=move_line, move=move)
        current_move = move_line.move_id if move_line else move

        if current_move and current_move.sale_line_id:
            price = current_move.sale_line_id.price_unit
            currency = current_move.sale_line_id.currency_id
            res["line_key"] = f"{res['line_key']}_{str(price)}_{currency.id}"
            res["unit_price"] = price
            res["currency_id"] = currency

        return res
