# Copyright 2022 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_aggregated_product_quantities(self, **kwargs):
        """Odoo displays products non delivered in main table.
        So I remove key from it to be displayed in the bottom table
        """
        aggregated_move_lines = super()._get_aggregated_product_quantities(**kwargs)
        keys_to_remove = set()
        for aggregated_move_line in aggregated_move_lines:
            if not aggregated_move_lines[aggregated_move_line]["qty_done"]:
                keys_to_remove.add(aggregated_move_line)
        # To avoid change dict size on iteration
        for key_to_remmove in keys_to_remove:
            aggregated_move_lines.pop(key_to_remmove, None)
        return aggregated_move_lines
