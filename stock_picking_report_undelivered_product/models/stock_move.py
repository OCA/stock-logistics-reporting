# Copyright 2020 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    splitted_stock_move_orig_id = fields.Many2one(
        comodel_name="stock.move", string="Splitted from", readonly=True
    )

    def _prepare_move_split_vals(self, qty):
        """
        Store origin stock move which create splitted move.
        """
        vals = super()._prepare_move_split_vals(qty)
        vals["splitted_stock_move_orig_id"] = self.id
        return vals
