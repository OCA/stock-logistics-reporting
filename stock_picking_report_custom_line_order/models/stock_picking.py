# Copyright 2025 Foodles (https://www.foodles.co/).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_moves_for_report_picking(self):
        self.ensure_one()
        return self.move_ids_without_package
