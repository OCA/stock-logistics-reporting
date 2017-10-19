# -*- coding: utf-8 -*-
# Copyright 2014 Pedro M. Baeza - Tecnativa <pedro.baeza@tecnativa.com>
# Copyright 2015 Antonio Espinosa - Tecnativa <antonio.espinosa@tecnativa.com>
# Copyright 2016 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# Copyright 2017 Luis M. Ontalba - Tecnativa <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"

    currency_id = fields.Many2one(
        related='sale_line.currency_id', readonly=True,
        string='Currency')
    sale_line = fields.Many2one(
        comodel_name='sale.order.line',
        compute='_compute_sale_order_line_fields',
        string="Related order line")
    sale_tax_id = fields.Many2many(
        comodel_name='account.tax',
        compute='_compute_sale_order_line_fields',
        string="Taxes")
    sale_tax_description = fields.Char(
        compute='_compute_sale_order_line_fields',
        string='Tax Description')
    sale_price_unit = fields.Float(
        compute='_compute_sale_order_line_fields',
        digits=dp.get_precision('Product Price'),
        string="Sale price unit")
    sale_discount = fields.Float(
        compute='_compute_sale_order_line_fields',
        digits=dp.get_precision('Discount'),
        string="Sale discount (%)")
    sale_price_subtotal = fields.Monetary(
        compute='_compute_sale_order_line_fields',
        string="Price subtotal")
    sale_price_tax = fields.Float(
        compute='_compute_sale_order_line_fields',
        string='Taxes')
    sale_price_total = fields.Monetary(
        compute='_compute_sale_order_line_fields',
        string='Total')

    @api.multi
    def _compute_sale_order_line_fields(self):
        for operation in self:
            sale_lines = operation.mapped(
                'linked_move_operation_ids.move_id.procurement_id.'
                'sale_line_id')
            operation.update(operation.sale_lines_values(sale_lines))

    @api.multi
    def sale_lines_values(self, sale_lines):
        sum_qty = sum_price = sum_discount = sum_amount_untaxed = 0.0
        sum_amount_tax = sum_amount_total = 0.0
        rm = sale_lines[0].order_id.company_id.tax_calculation_rounding_method
        for sale_line in sale_lines:
            sum_qty += sale_line.product_uom_qty
            sum_price += sale_line.price_unit * sale_line.product_uom_qty
            sum_discount += sale_line.discount * sale_line.product_uom_qty
            amount_untaxed = sale_line.product_uom_qty * (
                sale_line.price_unit * (
                    1 - (sale_line.discount or 0.0) / 100.0))
            sum_amount_untaxed += amount_untaxed
            price = sale_line.price_unit * (1 - (sale_line.discount or
                                                 0.0) / 100)
            taxes = sale_line.tax_id.compute_all(
                price,
                sale_line.currency_id,
                sale_line.product_uom_qty,
                product=sale_line.product_id,
                partner=sale_line.order_id.partner_id
            )
            if rm == 'round_globally':
                amount_tax = sum(
                    t.get('amount', 0.0) for t in taxes.get('taxes', []))
            else:
                amount_tax = taxes['total_included'] - taxes['total_excluded']
            sum_amount_tax += amount_tax
            sum_amount_total += amount_untaxed + amount_tax
        sale_line = sale_lines[:1]
        return {
            'sale_line': sale_line,
            'sale_tax_description': ', '.join(map(lambda x: (
                x.description or x.name), sale_lines.mapped('tax_id'))),
            'sale_price_unit': sum_price / (sum_qty or 1),
            'sale_discount': sum_discount / (sum_qty or 1),
            'sale_price_subtotal': sum_amount_untaxed,
            'sale_price_tax': sum_amount_tax,
            'sale_price_total': sum_amount_total,
        }
