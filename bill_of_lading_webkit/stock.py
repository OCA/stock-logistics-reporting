# -*- encoding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from openerp.osv import fields, orm


class StockPickingOutWarehouse(orm.Model):
    _inherit = "stock.picking.out"
    _columns = {
        'manual_warehouse_id': fields.many2one(
            'stock.warehouse',
            'Picking from',
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'confirmed': [('readonly', False)],
                'assigned': [('readonly', False)],
            }
        ),
    }


class StockPickingInWarehouse(orm.Model):
    _inherit = "stock.picking.in"
    _columns = {
        'manual_warehouse_id': fields.many2one(
            'stock.warehouse',
            'Deliver to',
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'confirmed': [('readonly', False)],
                'assigned': [('readonly', False)],
            }
        ),
    }


class StockPickingWarehouse(orm.Model):
    _inherit = "stock.picking"
    _columns = {
        'manual_warehouse_id': fields.many2one(
            'stock.warehouse',
            'Warehouse',
            readonly=True,
            states={
                'draft': [('readonly', False)],
                'confirmed': [('readonly', False)],
                'assigned': [('readonly', False)],
            }
        ),
    }
