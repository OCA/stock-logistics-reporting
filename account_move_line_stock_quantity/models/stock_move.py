# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_account_move_line_vals(self):
        vals_list = super()._get_account_move_line_vals()
        if self.is_in:
            signed_qty = self._get_valued_qty()
        elif self.is_out:
            signed_qty = -self._get_valued_qty()
        else:
            signed_qty = 0.0
        valuation_account_id = self.product_id._get_product_accounts()[
            "stock_valuation"
        ].id
        for vals in vals_list:
            vals["stock_quantity"] = (
                signed_qty if vals["account_id"] == valuation_account_id else 0.0
            )
        return vals_list
