# -*- coding: utf-8 -*-
# Copyright 2014 Pedro M. Baeza - Tecnativa <pedro.baeza@tecnativa.com>
# Copyright 2015 Antonio Espinosa - Tecnativa <antonio.espinosa@tecnativa.com>
# Copyright 2016 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp


class StockPackOperation(models.Model):
    _inherit = "stock.pack.operation"

    currency_id = fields.Many2one(
        related='sale_line.currency_id',
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
        if len(sale_lines) <= 1:
            price_unit = sale_lines.price_unit
            discount = sale_lines.discount
        else:
            sum_qty = 0.0
            sum_price = 0.0
            sum_discount = 0.0
            for sale_line in sale_lines:
                sum_qty += sale_line.product_uom_qty
                sum_price += sale_line.price_unit * sale_line.product_uom_qty
                sum_discount += sale_line.discount * sale_line.product_uom_qty
            price_unit = sum_price / (sum_qty or 1)
            discount = sum_discount / (sum_qty or 1)
        price_reduce = price_unit * (1 - (discount or 0.0) / 100.0)
        sale_line = sale_lines[:1]
        sale_tax = sale_line.tax_id
        taxes = sale_tax.compute_all(
            price_unit=price_reduce,
            currency=sale_line.currency_id,
            quantity=self.product_qty,
            product=sale_line.product_id,
            partner=sale_line.order_id.partner_id)
        if sale_line.company_id.tax_calculation_rounding_method == (
                'round_globally'):
            price_tax = sum(
                t.get('amount', 0.0) for t in taxes.get('taxes', []))
        else:
            price_tax = taxes['total_included'] - taxes['total_excluded']
        return {
            'sale_line': sale_line,
            'sale_tax_id': sale_tax,
            'sale_tax_description': ', '.join(map(lambda x: (
                x.description or x.name), sale_tax)),
            'sale_price_unit': price_unit,
            'sale_discount': discount,
            'sale_price_subtotal': taxes['total_excluded'],
            'sale_price_tax': price_tax,
            'sale_price_total': taxes['total_included'],
        }
