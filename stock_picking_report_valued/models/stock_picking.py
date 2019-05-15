# Copyright 2014-2018 Tecnativa - Pedro M. Baeza
# Copyright 2015 Antonio Espinosa - Tecnativa <antonio.espinosa@tecnativa.com>
# Copyright 2016 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# Copyright 2016 Luis M. Ontalba - Tecnativa <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    valued = fields.Boolean(
        related='partner_id.valued_picking', readonly=True,
    )
    currency_id = fields.Many2one(
        related='sale_id.currency_id', readonly=True,
        string='Currency',
        related_sudo=True,  # See explanation for sudo in compute method
    )
    amount_untaxed = fields.Monetary(
        compute='_compute_amount_all',
        string='Untaxed Amount',
        compute_sudo=True,  # See explanation for sudo in compute method
    )
    amount_tax = fields.Monetary(
        compute='_compute_amount_all',
        string='Taxes',
        compute_sudo=True,
    )
    amount_total = fields.Monetary(
        compute='_compute_amount_all',
        string='Total',
        compute_sudo=True,
    )

    @api.multi
    def _compute_amount_all(self):
        """This is computed with sudo for avoiding problems if you don't have
        access to sales orders (stricter warehouse users, inter-company
        records...).
        """
        for pick in self:
            sale = pick.sale_id
            round_method = sale.company_id.tax_calculation_rounding_method
            if round_method == 'round_globally':
                amount_untaxed = sum(pick.move_line_ids.mapped(
                    'sale_price_subtotal'))
                amount_tax = sum(pick.move_line_ids.mapped(
                    'sale_price_tax'))
            else:
                round_curr = sale.currency_id.round
                amount_untaxed = amount_tax = 0.0
                for tax_id, tax_group in pick.get_taxes_values().items():
                    amount_untaxed += round_curr(tax_group['base'])
                    amount_tax += round_curr(tax_group['amount'])
            pick.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.move_line_ids:
            tax = line.sale_line.tax_id
            tax_id = tax.id
            if tax_id not in tax_grouped:
                tax_grouped[tax_id] = {
                    'amount': line.sale_price_tax,
                    'base': line.sale_price_subtotal,
                    'tax': tax,
                }
            else:
                tax_grouped[tax_id]['amount'] += line.sale_price_tax
                tax_grouped[tax_id]['base'] += line.sale_price_subtotal
        return tax_grouped
