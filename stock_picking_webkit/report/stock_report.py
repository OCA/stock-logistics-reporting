# -*- coding: utf-8 -*-
##############################################################################
#
#   Copyright (c) 2011-2013 Camptocamp SA (http://www.camptocamp.com)
#   @author Nicolas Bessi
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

import operator
from report import report_sxw
import pooler


class NullMove(object):
    """helper class to generate empty lines in the delivery report"""
    def __init__(self):
        self.product_id = NullObj()
        self.picking_id = NullObj()
        self.product_qty = ''


class NullObj(object):
    """the null obj has any attribute you want
    with an empty string as the value"""
    def __getattr__(self, attr):
        return ''


class PickingAgregation(object):

    def __init__(self, src_stock, dest_stock, stock_moves):
        self.src_stock = src_stock
        self.dest_stock = dest_stock
        self.stock_moves = stock_moves

    def exists(self):
        return False

    def __hash__(self):
        return hash((self.src_stock.id, self.dest_stock.id))

    def __eq__(self, other):
        return (self.src_stock.id,
                self.dest_stock.id) == (other.src_stock.id,
                                        other.dest_stock.id)

    def moves_by_product(self):
        """iterate over moves sorted by product default_code"""
        return sorted(self.stock_moves,
                      key=operator.attrgetter('product_id.default_code'))

    def moves_by_sale_order(self):
        """iterate over moves sorted by sale order name

        a NullMove is inserted when for each new sale order so that
        the report displays an empty line
        """
        origin = None
        for move in sorted(self.stock_moves,
                           key=operator.attrgetter('picking_id.origin')):
            if origin is None:
                origin = move.picking_id.origin
            else:
                if move.picking_id.origin != origin:
                    yield NullMove()
                    origin = move.picking_id.origin
            yield move

    def product_quantity(self):
        """iterate over the different products concerned by the moves
        with their total quantity, sorted by product default_code"""
        products = {}
        product_qty = {}
        for move in self.stock_moves:
            p_code = move.product_id.default_code
            products[p_code] = move.product_id
            if p_code not in product_qty:
                product_qty[p_code] = move.product_qty
            else:
                product_qty[p_code] += move.product_qty
        for p_code in sorted(products):
            yield products[p_code], product_qty[p_code]


class PrintPick(report_sxw.rml_parse):

    def __init__(self, cursor, uid, name, context):
        super(PrintPick, self).__init__(cursor, uid, name, context=context)
        self.pool = pooler.get_pool(self.cr.dbname)
        self.cursor = self.cr

        self.numeration_type = False
        self.localcontext.update({})

    def _get_form_param(self, param, data, default=False):
        return data.get('form', {}).get(param, default) or default

    def set_context(self, objects, data, ids, report_type=None):
        """Return res.partner.category"""
        # !! data form is manually set in wizard
        agreg = {}
        for pick in objects:
            for move in pick.move_lines:
                if move.state == 'assigned':
                    key = (move.location_id, move.location_dest_id)
                    agreg.setdefault(key, []).append(move)
        objects = []
        for agr in agreg:
            print agr
            objects.append(PickingAgregation(agr[0], agr[1], agreg[agr]))
        return super(PrintPick, self).set_context(objects,
                                                  data,
                                                  ids,
                                                  report_type=report_type)

report_sxw.report_sxw('report.webkit.aggregated_picking',
                      'stock.picking',
                      'addons/stock_picking_webkit/report/picking.html.mako',
                      parser=PrintPick)

report_sxw.report_sxw('report.webkit.aggregated_delivery',
                      'stock.picking',
                      'addons/stock_picking_webkit/report/delivery.html.mako',
                      parser=PrintPick)
