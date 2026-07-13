# Copyright 2023 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _is_to_external_location(self):
        self.ensure_one()
        return (
            super()._is_to_external_location() or self.picking_type_code == "internal"
        )
