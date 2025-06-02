# Copyright 2025 Foodles (https://www.foodles.co/).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def get_move_lines_for_report_picking(self):
        self.ensure_one()
        return self.move_line_ids.sorted(key=lambda ml: ml.location_id.id)
