# Copyright 2020 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    undelivered_product_slip_report_method = fields.Selection(
        string="Method to display undelivered product lines in report picking",
        related="company_id.undelivered_product_slip_report_method",
        readonly=False,
    )


class Company(models.Model):
    _inherit = "res.company"

    undelivered_product_slip_report_method = fields.Selection(
        [
            ("all", "Display all undelivered product lines"),
            (
                "partially_undelivered",
                "Display only partially undelivered product lines",
            ),
            (
                "completely_undelivered",
                "Display only completely undelivered product lines",
            ),
        ],
        string="Method to display undelivered product lines in report picking",
        default="all",
    )
