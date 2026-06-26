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
                bom_line = bom.bom_line_ids.filtered(
                    lambda line: line.product_id == self.product_id
                )[:1]
                if bom_line:
                    component_qty = bom_line.product_uom_id._compute_quantity(
                        bom_line.product_qty,
                        self.product_uom,
                        round=False,
                    )
                    bom_qty = bom.product_uom_id._compute_quantity(
                        bom.product_qty,
                        sale_line.product_uom_id,
                        round=False,
                    )
                    result = component_qty / bom_qty if bom_qty else 0.0
        return result
