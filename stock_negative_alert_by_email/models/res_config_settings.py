# Copyright (C) 2025-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettingInherit(models.TransientModel):
    _inherit = "res.config.settings"

    negative_stock_mail_from = fields.Char(
        related="company_id.negative_stock_mail_from",
        readonly=False,
    )
    negative_stock_mail_to = fields.Char(
        related="company_id.negative_stock_mail_to",
        readonly=False,
    )
    negative_stock_interval_number = fields.Integer(
        related="company_id.negative_stock_interval_number",
        readonly=False,
    )
    negative_stock_interval_type = fields.Selection(
        related="company_id.negative_stock_interval_type",
        readonly=False,
    )
    negative_stock_quantity_type = fields.Selection(
        related="company_id.negative_stock_quantity_type",
        readonly=False,
    )
