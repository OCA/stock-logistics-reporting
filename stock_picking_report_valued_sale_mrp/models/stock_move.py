# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_components_per_kit(self):
        """Compute how many kit components were demanded from this line.
        We rely on the matching of sale order and pickings demands, but if those
        were manually changed, it could lead to inconsistencies"""
        self.ensure_one()
        result = 0.0
        sale_line = self.sale_line_id
        if sale_line:
            product = sale_line.product_id
            bom = (
                self.env["mrp.bom"]
                ._bom_find(
                    product,
                    company_id=self.company_id.id,
                )
                .get(product)
            )
            if bom and bom.type == "phantom" and sale_line.product_uom_qty:
                component_demand = sum(
                    sale_line.move_ids.filtered(
                        lambda x: x.product_id == self.product_id
                        and not x.origin_returned_move_id
                        and (
                            x.state != "cancel"
                            or (x.state == "cancel" and x.picking_id.backorder_id)
                        )
                    ).mapped("product_uom_qty")
                )
                result = component_demand / sale_line.product_uom_qty
        return result
