# Copyright 2024 Bernat Obrador
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    product_total_price = fields.Float(
        compute="_compute_product_total_price",
        string="Total Product Price",
        store=True,
    )

    @api.depends("product_id", "quantity")
    def _compute_product_total_price(self):
        for record in self:
            record.product_total_price = record.product_id.lst_price * record.quantity
