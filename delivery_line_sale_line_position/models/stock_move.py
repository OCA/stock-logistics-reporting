# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    position_sale_line = fields.Char(
        related="sale_line_id.position_formatted",
        string="Position",
    )
