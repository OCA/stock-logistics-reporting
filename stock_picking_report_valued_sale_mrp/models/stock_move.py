# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_components_per_kit(self):
        """Compute how many kit components there are per kit of this line.
        They are taken from the kit BoM when the move tells it (see
        _get_components_per_kit_from_bom). Otherwise we rely on the matching
        of sale order and pickings demands, but if those were manually
        changed, it could lead to inconsistencies.

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
            or not sale_line.product_uom_qty
        ):
            return 0.0
        components_per_kit = self._get_components_per_kit_from_bom()
        if components_per_kit:
            return components_per_kit
        is_return_line = (
            float_compare(
                sale_line.product_uom_qty,
                0,
                precision_rounding=sale_line.product_uom.rounding,
            )
            < 0
        )
        # Moves returning the demand of the line are not demand themselves.
        demand_moves = sale_line.move_ids.filtered(
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
        return component_demand / abs(sale_line.product_uom_qty)

    def _get_components_per_kit_from_bom(self):
        """Components of this move's product per kit unit of the sale line,
        from the kit BoM, so deliveries and returns don't change it. 0.0 when
        it can't be told, so the caller falls back to the demand ratio: the
        kit BoM isn't in the moves, a move of the product doesn't come from
        it, or the component is rounded and the line was exploded more than
        once.

        As sale_mrp does to compute the delivered kits, the BoM is exploded
        for the whole sale line and its current quantities are used. explode
        rounds each component up, and the moves of a line exploded more than
        once (quantity raised after confirming) are rounded on their own, so
        they don't match the BoM of the whole line."""
        self.ensure_one()
        sale_line = self.sale_line_id
        kit_bom = self._get_sale_kit_bom()
        if not kit_bom or not sale_line.product_uom_qty:
            return 0.0
        sale_qty = abs(sale_line.product_uom_qty)
        bom_lines, line_qty = self._explode_sale_kit_bom(kit_bom, sale_qty)
        _one_kit_lines, one_kit_qty = self._explode_sale_kit_bom(kit_bom, 1.0)
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        product_moves = sale_line.move_ids.filtered(
            lambda m: m.product_id == self.product_id
        )
        if float_compare(line_qty, one_kit_qty * sale_qty, precision_digits=precision):
            # Rounded component: the BoM only tells what the moves hold when
            # the line was exploded once.
            exploded_qty = sum(
                move.product_uom._compute_quantity(
                    move.product_uom_qty, self.product_uom, round=False
                )
                # The rest of a move validated without backorder is cancelled
                # in the done picking: it was exploded with the line.
                for move in product_moves.filtered(
                    lambda m: not m.origin_returned_move_id
                    and (m.state != "cancel" or m.picking_id.state == "done")
                )
            )
            if float_compare(exploded_qty, line_qty, precision_digits=precision):
                return 0.0
        # The caller adds up every move line of the product, so every move of
        # the product must come from these BoM lines.
        if product_moves.filtered(lambda m: not m.bom_line_id) or (
            product_moves.bom_line_id - bom_lines
        ):
            return 0.0
        return line_qty / sale_qty

    def _explode_sale_kit_bom(self, kit_bom, kits):
        """BoM lines of this move's product and their quantity, in the move
        UoM, for ``kits`` kits of the sale line, with the same factor as
        stock.move.action_explode."""
        sale_line = self.sale_line_id
        _boms, lines = kit_bom.explode(
            sale_line.product_id,
            sale_line.product_uom._compute_quantity(kits, kit_bom.product_uom_id)
            / kit_bom.product_qty,
        )
        bom_lines = self.env["mrp.bom.line"]
        qty = 0.0
        for line, line_data in lines:
            if line.product_id == self.product_id:
                bom_lines |= line
                qty += line.product_uom_id._compute_quantity(
                    line_data["qty"], self.product_uom, round=False
                )
        return bom_lines, qty

    def _get_sale_kit_bom(self):
        """Kit BoM of the sale line the move was exploded with. A component of
        an inner kit points to the inner BoM, so it's taken from the moves of
        the same picking that come straight from the kit BoM; none or more
        than one (a BoM replaced between explosions) can't tell it."""
        self.ensure_one()
        product = self.sale_line_id.product_id

        def is_kit_bom(bom):
            return bom.type == "phantom" and (
                bom.product_id == product
                or (
                    not bom.product_id
                    and bom.product_tmpl_id == product.product_tmpl_id
                )
            )

        if is_kit_bom(self.bom_line_id.bom_id):
            return self.bom_line_id.bom_id
        boms = self.sale_line_id.move_ids.filtered(
            lambda m: m.picking_id == self.picking_id
        ).bom_line_id.bom_id.filtered(is_kit_bom)
        return boms if len(boms) == 1 else self.env["mrp.bom"]

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
