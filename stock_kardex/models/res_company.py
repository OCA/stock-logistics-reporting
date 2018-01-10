# -*- coding: utf-8 -*-
# © <2018> <Jarsa Sistemas, S.A. de C.V.>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    location_id = fields.Many2one(
        'stock.location',
        string="Location",)
