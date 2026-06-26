# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_picking_operations_lang(self):
        self.ensure_one()
        warehouse = self.picking_type_id.warehouse_id
        if (
            warehouse.picking_operation_language_option == "partner"
            and self.partner_id.lang
        ):
            return self.partner_id.lang
        if (
            warehouse.picking_operation_language_option == "warehouse"
            and warehouse.warehouse_language
        ):
            return warehouse.warehouse_language
        return self._get_report_lang() or self.env.user.lang or self.env.lang
