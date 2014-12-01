# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com> 
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, orm
from openerp.addons.decimal_precision import decimal_precision as dp

class StockPicking(orm.Model):
    _inherit = "stock.picking"

    def _get_currency_id(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            res[picking.id] = False
            total_tax = 0.0
            for move in picking.move_lines:
                if not move.sale_line_id:
                    continue
                # Take one of the sale order lines currencies (it would be
                # alwaysthe same for all) 
                res[picking.id] = move.sale_line_id.order_id.currency_id.id
                break
        return res

    def _amount_untaxed(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            res[picking.id] = 0.0
            for move in picking.move_lines:
                res[picking.id] += move.sale_price_subtotal
        return res

    def _amount_tax(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        tax_obj = self.pool['account.tax']
        cur_obj = self.pool['res.currency']
        for picking in self.browse(cr, uid, ids, context=context):
            cur = False
            total_tax = 0.0
            for move in picking.move_lines:
                if not move.sale_line_id:
                    continue
                price_unit = (move.sale_price_unit *
                              (100 - move.sale_discount or 0.0) / 100.0)
                for c in tax_obj.compute_all(cr, uid, move.sale_line_id.tax_id,
                                         price_unit,
                                         move.product_qty, move.product_id,
                                         move.sale_line_id.order_id.partner_id
                                         )['taxes']:
                    total_tax += c.get('amount', 0.0)
            res[picking.id] = (picking.currency_id and
                               cur_obj.round(cr, uid, picking.currency_id,
                                             total_tax)
                               or 0.0)
        return res

    def _amount_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            res[picking.id] = picking.amount_untaxed + picking.amount_tax
        return res

    _columns = {
        'currency_id': fields.related('sale_id', 'currency_id',
                       type="many2one", relation="res.currency",
                       store=True, string='Sale currency', readonly=True),
        'amount_untaxed': fields.function(_amount_untaxed, type="float",
                        digits_compute=dp.get_precision('Account'),
                        method=True, string='Untaxed amount', readonly=True),
        'amount_tax': fields.function(_amount_tax, type="float",
                        digits_compute=dp.get_precision('Account'),
                        method=True, string='Taxes', readonly=True),
        'amount_total': fields.function(_amount_total, type="float",
                        digits_compute=dp.get_precision('Account'),
                        method=True, string='Total', readonly=True),
    }

class StockPickingOut(orm.Model):
    _inherit = "stock.picking.out"

    def __init__(self, pool, cr):
        super(StockPickingOut, self).__init__(pool, cr)
        picking_obj = self.pool['stock.picking']
        for field_name in ('currency_id', 'amount_untaxed', 'amount_tax',
                           'amount_total'):
            self._columns[field_name] = picking_obj._columns[field_name]