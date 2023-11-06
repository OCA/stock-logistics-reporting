# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import datetime

from odoo import fields, models

from .stock_move_line import get_aggregated_properties


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move", "display.line.mixin"]

    sequence = fields.Integer(related="sale_line_id.sequence", store=True)
    previous_line_id = fields.Many2one(related="sale_line_id.previous_line_id")
    next_line_id = fields.Many2one(related="sale_line_id.next_line_id")

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
            "name": order_line.name,
            "date": datetime.datetime.now(),
            "company_id": order_line.company_id.id,
            "product_id": False,
            "product_uom_qty": 0,
            "product_uom": False,
            "location_id": False,
            "location_dest_id": False,
            "procure_method": False,
        }

    def _aggregate_sections_and_notes(self, aggregated_move_lines, done_line_keys):
        """Insert at the right position any sections or notes related
        to a move

        :param aggregated_move_lines: the aggregated dict of lines
        :param done_line_keys: a list of line keys to avoid to process twice
        """
        line_key, name, description, uom = get_aggregated_properties(move=self)
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
