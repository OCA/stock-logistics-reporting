# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def write(self, vals):
        res = super().write(vals)
        if vals.get("name"):
            self.move_ids.description_picking = vals["name"]
        return res
