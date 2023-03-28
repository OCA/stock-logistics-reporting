# Copyright 2023 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    external_note = fields.Html(
        help="External note to be printed in external reports like Delivery Slip",
    )
