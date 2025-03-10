# Copyright 2023 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def should_print_delivery_address(self):
        self.ensure_one()
        if (
            self.move_ids
            and (self.move_ids[0].partner_id or self.partner_id)
            and (
                self._is_to_external_location() or self.picking_type_code == "internal"
            )
        ):
            return True
        return super().should_print_delivery_address()
