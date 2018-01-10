# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockKardexGeneral(models.AbstractModel):
    _name = "stock.kardex.general"
    _description = "General Ledger Report"
    _inherit = "stock.report"

    filter_date = {
        'date_from': '',
        'date_to': '',
        'filter': 'custom'}
    filter_product = True
    filter_unfold_all = False

    def get_columns_name(self, options):
        return [{'name': ''},
                {'name': _("Type")},
                {'name': _("Date"), 'class': 'date'},
                {'name': _("Quantity"), 'class': 'number'},
                {'name': _("UoM")},
                {'name': _("Balance"), 'class': 'number'}]

    @api.model
    def do_query(self, options, line_id=False):
        pp_obj = self.env['product.product']
        uom_obj = self.env['product.uom']
        results = {}
        context = self.env.context
        location_id = self.env.user.company_id.location_id.id
        if not location_id:
            raise ValidationError(
                _("Verify that a main warehouse is"
                  " configured for the report."))
        select = (
            """SELECT sml.product_id, sml.reference, sml.qty_done, sml.date,
            sml.id, sml.location_id, sml.location_dest_id, sml.state,
            sml.product_uom_id
            FROM stock_move_line sml
            WHERE sml.state = 'done' AND (
                sml.location_id = %s OR sml.location_dest_id = %s)
                AND sml.date >= %s AND sml.date <= %s
            """)
        if line_id:
            select += 'AND sml.product_id = %s' % line_id
        elif context.get('filter_product_ids') and len(
                context['filter_product_ids'].ids) > 1:
            select += 'AND sml.product_id IN %s' % (tuple(
                context['filter_product_ids'].ids), )
        elif context.get('filter_product_ids') and len(
                context['filter_product_ids'].ids) == 1:
            select += 'AND sml.product_id = %s' % context[
                'filter_product_ids'].id
        select += ' ORDER BY sml.date'
        if not options['date']['date_from'] or not options['date']['date_to']:
            options['date']['date_from'] = self.get_date_start()
            options['date']['date_to'] = self.get_date_end()
        self.env.cr.execute(
            select, (location_id, location_id, options['date']['date_from'],
                     options['date']['date_to']))
        query_data = self.env.cr.dictfetchall()
        for item in query_data:
            product = pp_obj.browse(item['product_id'])
            uom_id = uom_obj.browse(item['product_uom_id'])
            qty_done = uom_id._compute_quantity(
                item['qty_done'], product.uom_id)
            if item['product_id'] not in results.keys():
                results[item['product_id']] = []
            results[item['product_id']].append({
                'location_id': item['location_id'],
                'location_dest_id': item['location_dest_id'],
                'qty_done': (
                    qty_done if item['location_dest_id'] == location_id
                    else -qty_done),
                'date': item['date'],
                'move_id': item['id'],
                'move_name': item['reference'],
            })
        return results

    @api.model
    def get_lines(self, options, line_id=None):
        lines = []
        location = self.env.user.company_id.location_id.id
        if not location:
            raise ValidationError(
                _("Verify that a main warehouse is"
                  " configured for the report."))
        product_obj = self.env['product.product']
        stock_location_obj = self.env['stock.location']
        context = self.env.context
        dt_from = options['date'].get('date_from')
        line_id = line_id and int(line_id.split('_')[1]) or None
        data = self.with_context(
            date_from_aml=dt_from,
            date_from=dt_from).do_query(options, line_id)
        unfold_all = context.get('print_mode', False) and len(
            options.get('unfolded_lines')) == 0
        for product_id, moves in data.items():
            domain_lines = []
            product = product_obj.browse(product_id)
            balance = 0
            date_from_str = options['date']['date_from']
            stock_date_to = fields.Date.to_string(
                fields.Date.from_string(date_from_str) -
                timedelta(days=1))
            balance = product._compute_quantities_dict(
                self._context.get('lot_id', False),
                self._context.get('owner_id', False),
                self._context.get('package_id', False),
                self._context.get('from_date', False),
                stock_date_to)
            if balance:
                balance = balance[product_id]['qty_available']
            lines.append({
                'id': 'product_%s' % (product_id),
                'name': product.name,
                'columns': (
                    [{'name': v} for v in [
                        product.uom_id.name,
                        sum([x['qty_done'] for x in moves])]]),
                'level': 2,
                'unfoldable': True,
                'unfolded': 'product_%s' % (
                    product_id) in options.get('unfolded_lines') or unfold_all,
                'colspan': 4,
            })
            if 'product_%s' % (
                    product_id) in options.get('unfolded_lines') or unfold_all:
                domain_lines = [{
                    'id': 'initial_%s' % (product_id),
                    'class': 'o_stock_reports_initial_balance',
                    'name': _('Initial Balance'),
                    'parent_id': 'product_%s' % (product_id),
                    'columns': [{'name': v} for v in [balance]],
                    'level': 4,
                    'colspan': 5,
                }]
                for line in moves:
                    location_id = stock_location_obj.browse(
                        line['location_id'])
                    location_dest_id = stock_location_obj.browse(
                        line['location_dest_id'])
                    balance += line['qty_done']
                    line_value = {
                        'id': line['move_id'],
                        'parent_id': 'product_%s' % (product_id),
                        'name': line['move_name'],
                        'columns': [{'name': v} for v in [
                            'IN <-- %s' % location_id.name if
                            line['location_dest_id'] == location
                            else 'OUT --> %s' %
                            location_dest_id.name, line['date'], line[
                                'qty_done'], '', balance]],
                        'level': 4,
                        'caret_options': 'stock.move.line',
                    }
                    domain_lines.append(line_value)
                lines += domain_lines
        return lines

    @api.model
    def get_report_name(self):
        return _("Stock Kardex")
