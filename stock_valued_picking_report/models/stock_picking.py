# -*- coding: utf-8 -*-
# Copyright 2014 Pedro M. Baeza - Tecnativa <pedro.baeza@tecnativa.com>
# Copyright 2015 Antonio Espinosa - Tecnativa <antonio.espinosa@tecnativa.com>
# Copyright 2016 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    valued = fields.Boolean(related='partner_id.valued_picking')
    currency_id = fields.Many2one(
        related='sale_id.currency_id',
        string='Currency')
    amount_untaxed = fields.Monetary(
        compute='_compute_amount_all',
        string='Untaxed Amount')
    amount_tax = fields.Monetary(
        compute='_compute_amount_all',
        string='Taxes')
    amount_total = fields.Monetary(
        compute='_compute_amount_all',
        string='Total')

    @api.multi
    def _compute_amount_all(self):
        for pick in self:
            amount_untaxed = sum(pick.pack_operation_ids.mapped(
                'sale_price_subtotal'))
            amount_tax = sum(pick.pack_operation_ids.mapped(
                'sale_price_tax'))
            pick.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })
