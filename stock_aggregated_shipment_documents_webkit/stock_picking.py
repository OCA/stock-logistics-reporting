# -*- coding: utf-8 -*-
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

from openerp.osv import orm


class StockPickingOut(orm.Model):
    _name = 'stock.picking.out'
    _inherit = 'stock.picking.out'

    def action_email_report(self, cr, uid, ids, context=None):
        # This function opens a window to compose an email,
        # with the pricelist template message loaded by default

        # This option should only be used for a single id at a time.
        assert len(ids) == 1

        ir_model_data = self.pool['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                cr, uid,
                'stock_aggregated_shipment_documents_webkit',
                'email_template_shipment_documents')[1]
        except ValueError:
            template_id = False

        try:
            compose_form_id = ir_model_data.get_object_reference(
                cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = dict(context)
        ctx.update({
            'default_model': 'stock.picking.out',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        # Full explanation of this return is here :
        # http://stackoverflow.com/questions/12634031
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
