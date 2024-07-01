# Copyright 2023 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import fields, models

REPORT_STICKER_POSITIONS = [
    ("top_right", "Top (right)"),
    ("bottom_left", "Bottom (left)"),
]


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    show_product_stickers = fields.Selection(
        selection=REPORT_STICKER_POSITIONS,
        help="Display Product Stickers on chosen position inside the report.",
    )
