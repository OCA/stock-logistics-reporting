# encoding: utf-8
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def do_print_picking(self):
        self.ensure_one()
        picking = self[0]
        action_name = picking.partner_id.picking_report_id \
            and picking.partner_id.picking_report_id.report_name \
            or 'stock.report_picking'
        return self.env['report'].get_action(self, action_name)
