# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_components_per_kit(self):
        """Compute how many kit components were demanded from this line. We
        rely on the matching of sale order and pickings demands, but if those
        were manually changed, it could lead to inconsistencies"""
        self.ensure_one()
        sale_line = self.sale_line_id
        if (
            not sale_line
            or not sale_line.product_id.get_components()
            or sale_line.product_id.ids == sale_line.product_id.get_components()
            or not sale_line.product_uom_qty
        ):
            return 0.0
        # Moves returning the demand of the line are not demand themselves.
        demand_moves = sale_line.move_ids.filtered(
            lambda x: x.product_id == self.product_id
            and not x.origin_returned_move_id
            and (
                x.state != "cancel"
                or (x.state == "cancel" and x.picking_id.backorder_id)
            )
        )
        # A fully returned delivery is no longer demanded, but the same line
        # can have been delivered again (cancel + re-confirm), adding a second
        # delivery: counting both would double the demand. Fully returned moves
        # are only discarded while a delivery is still live, so flows where the
        # return itself is returned keep a valid ratio instead of a zero one.
        component_demand = sum(
            demand_moves.filtered(lambda x: not self._is_fully_returned(x)).mapped(
                "product_uom_qty"
            )
        ) or max(demand_moves.mapped("product_uom_qty"), default=0.0)
        return component_demand / sale_line.product_uom_qty

    def _is_fully_returned(self, move):
        """Tell whether everything the move demanded has been returned."""
        returned_qty = sum(move.returned_move_ids.mapped("product_uom_qty"))
        return (
            float_compare(
                returned_qty,
                move.product_uom_qty,
                precision_rounding=move.product_uom.rounding,
            )
            >= 0
        )
