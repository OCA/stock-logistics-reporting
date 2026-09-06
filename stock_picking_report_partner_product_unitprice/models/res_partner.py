# Copyright 2026 NICO SOLUTIIONS - ENGERINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    picking_report_render_unitprice = fields.Boolean(
        string="Render Unit Price on Delivery Slip", company_dependent=True
    )
