# © 2025 Daniel Reis - Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    qty_variation = fields.Float(
        compute="_compute_qty_variation",
        store=True,
    )

    def _get_qty_variation_sign(self):
        self.ensure_one()
        if self.move_id._is_in():
            return 1
        elif self.move_id._is_out():
            return -1
        else:
            return 0

    @api.depends(
        "product_uom_qty", "product_qty", "location_id.usage", "location_dest_id.usage"
    )
    def _compute_qty_variation(self):
        for line in self:
            line.qty_variation = line.qty_done * line._get_qty_variation_sign()
