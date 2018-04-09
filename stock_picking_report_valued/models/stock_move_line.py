# Copyright 2014 Pedro M. Baeza - Tecnativa <pedro.baeza@tecnativa.com>
# Copyright 2015 Antonio Espinosa - Tecnativa <antonio.espinosa@tecnativa.com>
# Copyright 2016 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# Copyright 2018 Luis M. Ontalba - Tecnativa <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    currency_id = fields.Many2one(
        related='sale_line.currency_id', readonly=True,
        string='Currency')
    sale_line = fields.Many2one(
        related='move_id.sale_line_id', readonly=True,
        string="Related order line")
    sale_tax_description = fields.Char(
        compute='_compute_sale_tax_description',
        string='Tax Description')
    sale_price_unit = fields.Float(
        related='sale_line.price_unit', readonly=True,
        string="Sale price unit")
    sale_discount = fields.Float(
        related='sale_line.discount', readonly=True,
        string="Sale discount (%)")
    sale_price_subtotal = fields.Monetary(
        compute='_compute_amount',
        string="Price subtotal")
    sale_price_tax = fields.Float(
        compute='_compute_amount',
        string='Taxes')

    @api.multi
    @api.depends('sale_line.tax_id')
    def _compute_sale_tax_description(self):
        for line in self:
            line.sale_tax_description = ', '.join([(
                x.description or x.name) for x in line.sale_line.tax_id])

    @api.depends('product_uom_qty', 'sale_discount', 'sale_price_unit',
                 'sale_line.tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.sale_price_unit * (1 - (
                line.sale_discount or 0.0) / 100.0)
            if line.picking_id.state == 'done':
                qty = line.qty_done
            else:
                qty = line.product_uom_qty
            taxes = line.sale_line.tax_id.compute_all(
                price,
                line.currency_id, qty,
                product=line.sale_line.product_id,
                partner=line.sale_line.order_id.partner_shipping_id)
            line.update({
                'sale_price_tax': sum(
                    t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'sale_price_subtotal': taxes['total_excluded'],
            })
