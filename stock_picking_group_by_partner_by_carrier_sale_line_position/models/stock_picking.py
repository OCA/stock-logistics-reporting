# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_sorted_moves(self):
        self.ensure_one()
        return self.move_lines.sorted(
            lambda m: m.sale_line_id.order_id.id * 1000 + m.sale_line_id.position
        )

    def _get_sorted_move_lines(self):
        self.ensure_one()
        return self.move_line_ids.sorted(lambda l: l.move_id.sale_line_id.position)
