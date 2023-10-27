# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from collections import OrderedDict

from odoo import fields, models
from odoo.tools.float_utils import float_is_zero


def get_aggregated_properties(move_line=False, move=False):
    """Taken from stock.models.stock_move_line._get_aggregated_product_quantities"""
    move = move or move_line.move_id
    uom = move.product_uom or move_line.product_uom_id
    name = move.product_id.display_name
    description = move.description_picking
    if description == name or description == move.product_id.name:
        description = False
    product = move.product_id
    line_key = f"{product.id}_{product.display_name}_{description or ''}_{uom.id}"
    return (line_key, name, description, uom)


class StockMoveLine(models.Model):
    _name = "stock.move.line"
    _inherit = ["stock.move.line", "display.line.mixin"]

    sequence = fields.Integer(related="move_id.sequence", store=True)
    previous_line_id = fields.Many2one(related="move_id.previous_line_id")
    next_line_id = fields.Many2one(related="move_id.next_line_id")

    def prepare_section_or_note_values(self, order_line):
        """This method is intended to be used to `convert` a display line to
        the current model

        It is mainly used for display lines injection to delivery reports
        """
        self.ensure_one()
        assert order_line.is_section_or_note()
        return {
            "sequence": order_line.sequence,
            "display_type": order_line.display_type,
            "display_class": order_line.get_section_or_note_class(),
            "name": order_line.name,
            "description": order_line.name,
            "qty_done": 0,
            "qty_ordered": 0,
            "product_uom_id": False,
            "product_id": False,
        }

    def _aggregate_sections_and_notes(self, aggregated_move_lines, done_line_keys):
        """Insert at the right position any sections or notes related
        to a move_line

        :param aggregated_move_lines: the aggregated dict of lines
        :param done_line_keys: a list of line keys to avoid to process twice
        """
        line_key, name, description, uom = get_aggregated_properties(move_line=self)
        if line_key in done_line_keys:
            return done_line_keys, aggregated_move_lines
        done_line_keys.add(line_key)

        total_lines = len(aggregated_move_lines)
        # Manage positionning and itemization
        pos = list(aggregated_move_lines.keys()).index(line_key) if line_key in aggregated_move_lines else 0
        items = list(aggregated_move_lines.items())
        previous_record = self.previous_line_id
        while previous_record:
            line_key = f"{previous_record.id}_{previous_record.display_type}"
            if line_key not in done_line_keys:
                if previous_record.is_section_or_note():
                    values = self.prepare_section_or_note_values(previous_record)
                    items.insert(pos, (line_key, values))
                    done_line_keys.add(line_key)
            previous_record = previous_record.previous_line_id

        # Then we manage the last line to include any remaining section/notes
        if (pos + 1) == total_lines:
            next_record = self.next_line_id
            while next_record:
                line_key = f"{next_record.id}_{next_record.display_type}"
                if line_key not in done_line_keys:
                    if next_record.is_section_or_note():
                        values = self.prepare_section_or_note_values(next_record)
                        items.append((line_key, values))
                        done_line_keys.add(line_key)
                next_record = next_record.next_line_id

        # Reconstuction
        return done_line_keys, dict(items)

    def _reordered_aggregated_product_quantities(self, **kwargs):
        """Regain the sequence ordering from sale order lines
        Needed for proper section and notes positioning

        Beware ! this method calls super()._get_aggregated_product_quantities
        which is overriden below
        """
        super_aggregated_move_lines = super()._get_aggregated_product_quantities(
            **kwargs
        )
        new_aggregated_move_lines = OrderedDict()
        for move_line in self.sorted("sequence"):
            line_key, name, description, uom = get_aggregated_properties(
                move_line=move_line
            )
            agg_move_value = super_aggregated_move_lines.get(line_key)
            new_aggregated_move_lines[line_key] = agg_move_value
        return new_aggregated_move_lines

    def _get_aggregated_product_quantities(self, **kwargs):
        """This code partially take the content of the super method

        Especially for behaviors:
            - get_aggregated_properties subfonction
            - except_package context option
            - canceled or null quantity picking move lines
        """
        aggregated_move_lines = self._reordered_aggregated_product_quantities(**kwargs)

        # Keep track of section to be shown only once
        done_line_keys = set()
        for move_line in self.sorted("sequence"):
            if kwargs.get("except_package") and move_line.result_package_id:
                continue
            (
                done_line_keys,
                aggregated_move_lines,
            ) = move_line._aggregate_sections_and_notes(
                aggregated_move_lines, done_line_keys
            )

        if kwargs.get("strict"):
            return aggregated_move_lines

        # Loops to get backorders, backorders" backorders, and so and so...
        backorders = self.env["stock.picking"]
        pickings = self.picking_id
        while pickings.backorder_ids:
            backorders |= pickings.backorder_ids
            pickings = pickings.backorder_ids

        pickings = self.picking_id | backorders
        for empty_move in pickings.move_lines.sorted("sequence"):
            if not (
                empty_move.state == "cancel"
                and empty_move.product_uom_qty
                and float_is_zero(
                    empty_move.quantity_done,
                    precision_rounding=empty_move.product_uom.rounding,
                )
            ):
                continue
            (
                done_line_keys,
                aggregated_move_lines,
            ) = empty_move._aggregate_sections_and_notes(
                aggregated_move_lines, done_line_keys
            )

        return aggregated_move_lines
