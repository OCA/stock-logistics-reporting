# Copyright 2023 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    show_product_stickers = fields.Boolean(
        help="Show Product Stickers on Pickings of this type.",
    )
