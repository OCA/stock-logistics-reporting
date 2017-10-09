# -*- coding: utf-8 -*-
# Copyright 2017 Luis M. Ontalba - Tecnativa <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"

    sale_discount2 = fields.Float(
        compute='_compute_sale_order_line_fields',
        digits=dp.get_precision('Discount'),
        string="Sale discount 2 (%)")
    sale_discount3 = fields.Float(
        compute='_compute_sale_order_line_fields',
        digits=dp.get_precision('Discount'),
        string="Sale discount 3 (%)")

    @api.multi
    def sale_lines_values(self, sale_lines):
        discount_extra = (sale_lines.mapped('discount2') +
                          sale_lines.mapped('discount3'))
        if all(d == 0.0 for d in discount_extra):
            return super(StockPackOperation, self).sale_lines_values(
                sale_lines)
        sum_qty = 0.0
        sum_price = 0.0
        sum_discount = sum_discount2 = sum_discount3 = 0.0
        sum_amount_untaxed = 0.0
        sum_amount_tax = 0.0
        sum_amount_total = 0.0
        for sale_line in sale_lines:
            sum_qty += sale_line.product_uom_qty
            sum_price += sale_line.price_unit * sale_line.product_uom_qty
            sum_discount += sale_line.discount * sale_line.product_uom_qty
            sum_discount2 += sale_line.discount2 * sale_line.product_uom_qty
            sum_discount3 += sale_line.discount3 * sale_line.product_uom_qty
            amount_untaxed = sale_line.price_subtotal
            sum_amount_untaxed += amount_untaxed
            rm = sale_line.order_id.company_id.tax_calculation_rounding_method
            if rm == 'round_globally':
                taxes = sale_line.tax_id.compute_all(
                    sale_line.price_reduce,
                    sale_line.order_id.currency_id,
                    sale_line.product_uom_qty,
                    product=sale_line.product_id,
                    partner=sale_line.order_id.partner_shipping_id
                )
                amount_tax = sum(
                    t.get('amount', 0.0) for t in taxes.get('taxes', []))
            else:
                amount_tax = sale_line.price_tax
            sum_amount_tax += amount_tax
            sum_amount_total += amount_untaxed + amount_tax
        sale_line = sale_lines[:1]
        return {
            'sale_line': sale_line,
            'sale_tax_description': ', '.join(map(lambda x: (
                x.description or x.name), sale_lines.mapped('tax_id'))),
            'sale_price_unit': sum_price / (sum_qty or 1),
            'sale_discount': sum_discount / (sum_qty or 1),
            'sale_discount2': sum_discount2 / (sum_qty or 1),
            'sale_discount3': sum_discount3 / (sum_qty or 1),
            'sale_price_subtotal': sum_amount_untaxed,
            'sale_price_tax': sum_amount_tax,
            'sale_price_total': sum_amount_total,
        }
