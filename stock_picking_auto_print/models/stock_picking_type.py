# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    auto_print_delivery_slip = fields.Boolean(
        help="If this checkbox is ticked, Odoo will automatically print the delivery"
        "slip of a picking when it is validated.",
    )
