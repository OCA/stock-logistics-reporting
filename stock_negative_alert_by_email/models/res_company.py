# Copyright (C) 2025-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompanyInherit(models.Model):
    _inherit = "res.company"

    negative_stock_mail_from = fields.Char()
    negative_stock_mail_to = fields.Char()
    negative_stock_interval_number = fields.Integer()
    negative_stock_interval_type = fields.Selection(
        [
            ("minutes", "Minutes"),
            ("hours", "Hours"),
            ("days", "Days"),
            ("weeks", "Weeks"),
        ],
    )
    negative_stock_quantity_type = fields.Selection(
        [
            ("qty_available", "Quantity On Hand"),
            ("virtual_available", "Forecast Quantity"),
        ],
        default="qty_available",
    )
