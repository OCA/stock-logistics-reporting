# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_picking_operations_lang(self):
        warehouse = self.picking_type_id.warehouse_id
        if warehouse.picking_operation_language_option == "partner" and self.partner_id:
            return self.partner_id.lang
        if warehouse.picking_operation_language_option == "warehouse":
            return warehouse.warehouse_language
        return self.env.user.lang
