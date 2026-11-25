# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    show_pickup_address = fields.Boolean(
        string="Show Pick-up Address in report",
        help="Show Pick-up Address in Incoming Report",
    )
