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

class StockMove(orm.Model):
    _inherit = "stock.move"

    def _get_sale_price_subtotal(self, cr, uid, ids, field_name, arg,
                                  context=None):
        res = {}
        cur_obj = self.pool['res.currency']
        for move in self.browse(cr, uid, ids, context=context):
            res[move.id] = False
            if move.sale_line_id:
                subtotal = move.sale_price_unit * move.product_qty * \
                                    (1 - (move.sale_discount or 0.0) / 100.0)
                # Round by currency precision
                cur = move.sale_line_id.order_id.currency_id
                res[move.id] = cur_obj.round(cr, uid, cur, subtotal)
        return res

    _columns = {
        'sale_price_unit': fields.related('sale_line_id', 'price_unit',
                                      type="float", readonly=True,
                                      string="Sale price unit"),
        'sale_discount': fields.related('sale_line_id', 'discount',
                                    type="float", readonly=True,
                                    string="Sale discount (%)"),
        'sale_price_subtotal': fields.function(_get_sale_price_subtotal,
                                               string='Price subtotal',
                                               type='float', method=True,
                                               readonly=True),
    }
