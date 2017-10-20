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
        sum_qty = sum_discount2 = sum_discount3 = 0.0
        prev_price_unit = {}
        for sale_line in sale_lines:
            sum_qty += sale_line.product_uom_qty
            sum_discount2 += sale_line.discount2 * sale_line.product_uom_qty
            sum_discount3 += sale_line.discount3 * sale_line.product_uom_qty
            prev_price_unit['sale_line.id'] = sale_line.price_unit
            new_price = sale_line.price_unit * (
                1 - ((sale_line.discount2 or 0.0) / 100)) * (
                1 - ((sale_line.discount3 or 0.0) / 100))
            sale_line.update({
                'price_unit': new_price,
            })
        res = super(StockPackOperation, self).sale_lines_values(sale_lines)
        res['sale_discount2'] = sum_discount2 / (sum_qty or 1)
        res['sale_discount3'] = sum_discount3 / (sum_qty or 1)
        for sale_line in sale_lines:
            sale_line.update({
                'price_unit': prev_price_unit['sale_line.id']
            })
        return res
