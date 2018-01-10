# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    location_id = fields.Many2one(
        'stock.location',
        string="Location for Stock Kardex",
        compute="_get_location",
        inverse="_set_location",)

    @api.multi
    @api.depends('company_id')
    def _get_location(self):
        for rec in self:
            rec.location_id = rec.company_id.location_id.id

    @api.multi
    def _set_location(self):
        for rec in self:
            if rec.location_id != rec.company_id.location_id:
                rec.company_id.location_id = rec.location_id.id
