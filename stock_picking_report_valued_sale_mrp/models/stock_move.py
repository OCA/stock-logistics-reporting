# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.tools import float_compare, float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_components_per_kit(self):
        """Compute how many kit components were demanded from this line. We
        rely on the matching of sale order and pickings demands, but if those
        were manually changed, it could lead to inconsistencies.

        A negative sale line is a return: the core turns negative demand into
        return moves (see stock.move._action_confirm), so its moves are its
        own demand even when they are linked to the delivery they return.
        Only the moves returning a move of the same line (the return sent
        back to the customer) are left out."""
        self.ensure_one()
        sale_line = self.sale_line_id
        if (
            not sale_line
            or not sale_line.product_id.get_components()
            or sale_line.product_id.ids == sale_line.product_id.get_components()
        ):
            return 0
        rounding = sale_line.product_uom.rounding
        if float_is_zero(sale_line.product_uom_qty, precision_rounding=rounding):
            return 0
        is_return_line = (
            float_compare(sale_line.product_uom_qty, 0, precision_rounding=rounding) < 0
        )
        component_demand = sum(
            sale_line.move_ids.filtered(
                lambda x: x.product_id == self.product_id
                and (
                    not x.origin_returned_move_id
                    or (
                        is_return_line
                        and x.origin_returned_move_id.sale_line_id != sale_line
                    )
                )
                and (
                    x.state != "cancel"
                    or (x.state == "cancel" and x.picking_id.backorder_id)
                )
            ).mapped("product_uom_qty")
        )
        return component_demand / abs(sale_line.product_uom_qty)
