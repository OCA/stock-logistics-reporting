# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_components_per_kit(self):
        """Compute how many kit components were demanded from this line. We
        rely on the matching of sale order and pickings demands, but if those
        were manually changed, it could lead to inconsistencies"""
        self.ensure_one()
        sale_line = self.sale_line_id
        if not sale_line or not sale_line.product_id._is_phantom_bom():
            return 0
        component_demand = sum(
            sale_line.move_ids.filtered(
                lambda x: x.product_id == self.product_id
                and not x.origin_returned_move_id
                and (x.state != "cancel" or (x.state == "cancel" and x.backorder_id))
            ).mapped("product_uom_qty")
        )
        return component_demand / sale_line.product_uom_qty
