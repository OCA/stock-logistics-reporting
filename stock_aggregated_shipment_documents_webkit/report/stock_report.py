# -*- encoding: utf-8 -*-
# ##############################################################################
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

from openerp.report import report_sxw
from bill_of_lading_webkit.report.stock_report import BillOfLadingOut


class AggregatedShipping(BillOfLadingOut):
    def __init__(self, cr, uid, name, context):
        super(AggregatedShipping, self).__init__(cr, uid, name,
                                                 context=context)
        self.cr = cr
        self.uid = uid
        self.context = context
        self.localcontext.update({
            "merge_picking": self._merge_picking,
            "current_user": self._current_user,
        })

    def _current_user(self):
        return self.pool.get('res.users').browse(self.cr, self.uid, self.uid,
                                                 context=self.context)

    def _merge_picking(self, objects):
        # 1. Raise exception if not same partner
        partner_id = None
        partner = objects[0]
        move_lines = []
        for obj in objects:
            if not partner_id:
                partner_id = obj.partner_id.id
            elif obj.partner_id.id != partner_id:
                return None
            # merge move_lines
            [move_lines.append(line) for line in obj.move_lines]
        partner.move_lines = move_lines
        return partner


report_sxw.report_sxw('report.webkit.aggregate_shipping',
                      'stock.picking',
                      'aggregated_shipment_documents/report/aggregate_shipping.mako',
                      parser=AggregatedShipping)
