# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
#   (<https://www.eficent.com>)
# Copyright 2018 Aleph Objects, Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    stock_value = fields.Float(
        'Inventory Value', compute='_compute_inventory_value')
    account_value = fields.Float(
        'Accounting Value', compute='_compute_inventory_value')
    qty_at_date = fields.Float(
        'Inventory Quantity', compute='_compute_inventory_value')
    account_qty_at_date = fields.Float(
        'Accounting Quantity', compute='_compute_inventory_value')
    stock_fifo_real_time_aml_ids = fields.Many2many(
        'account.move.line', compute='_compute_inventory_value')
    stock_fifo_manual_move_ids = fields.Many2many(
        'stock.move', compute='_compute_inventory_value')

    def _compute_inventory_value(self):
        stock_move = self.env['stock.move']
        self.env['account.move.line'].check_access_rights('read')
        to_date = self.env.context.get('to_date', False)
        location = self.env.context.get('location', False)
        accounting_values = {}
        if not location:
            query = """
                SELECT aml.product_id, aml.account_id,
                sum(aml.debit) - sum(aml.credit), sum(quantity),
                array_agg(aml.id)
                FROM account_move_line AS aml
                WHERE aml.product_id IN %%s
                AND aml.company_id=%%s %s
                GROUP BY aml.product_id, aml.account_id"""
            params = (tuple(self._ids, ), self.env.user.company_id.id)
            if to_date:
                # pylint: disable=sql-injection
                query = query % ('AND aml.date <= %s',)
                params = params + (to_date,)
            else:
                query = query % ('',)
            self.env.cr.execute(query, params=params)
            res = self.env.cr.fetchall()
            for row in res:
                accounting_values[(row[0], row[1])] = (row[2], row[3],
                                                       list(row[4]))
        stock_move_domain = [
            ('product_id', 'in', self._ids),
            ('date', '<=', to_date)] + stock_move._get_all_base_domain()
        moves = stock_move.search(stock_move_domain)
        history = {}
        if to_date:
            query = """
                SELECT DISTINCT ON ("product_id") product_id, cost
                FROM   "product_price_history"
                WHERE datetime <= %s::date
                AND product_id IN %s
                ORDER  BY "product_id", "datetime" DESC NULLS LAST
                """
            args = (to_date, tuple(self._ids))
            self.env.cr.execute(query, args)
            for row in self.env.cr.dictfetchall():
                history.update({
                    row['product_id']: row['cost']
                })
        quantities_dict = self._compute_quantities_dict(
            self._context.get('lot_id'), self._context.get('owner_id'),
            self._context.get('package_id'), self._context.get('from_date'),
            self._context.get('to_date'))
        for product in self:
            qty_available = quantities_dict[product.id]['qty_available']
            # Retrieve the values from accounting
            # We cannot provide location-specific accounting valuation,
            # so better, leave the data empty in that case:
            if product.valuation == 'real_time' and not location:
                valuation_account_id = \
                    product.categ_id.property_stock_valuation_account_id.id
                value, quantity, aml_ids = accounting_values.get(
                    (product.id, valuation_account_id)) or (0, 0, [])
                product.account_value = value
                product.account_qty_at_date = quantity
                product.stock_fifo_real_time_aml_ids = \
                    self.env['account.move.line'].browse(aml_ids)
            # Retrieve the values from inventory
            if product.cost_method in ['standard', 'average']:

                price_used = product.standard_price
                if to_date:
                    price_used = history.get(product.id, 0)
                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available
            elif product.cost_method == 'fifo':
                if to_date:
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_value = sum(moves.mapped('value'))
                        product.qty_at_date = qty_available
                        product.stock_fifo_manual_move_ids = stock_move.browse(
                            moves.ids)
                else:
                    product.stock_value, moves = \
                        product._sum_remaining_values()
                    product.qty_at_date = qty_available
                    product.stock_fifo_manual_move_ids = moves

    def action_view_amls(self):
        self.ensure_one()
        to_date = self.env.context.get('to_date')
        tree_view_ref = self.env.ref('stock_account.view_stock_account_aml')
        form_view_ref = self.env.ref('account.view_move_line_form')
        action = {'name': _('Accounting Valuation at date'),
                  'type': 'ir.actions.act_window', 'view_type': 'form',
                  'view_mode': 'tree,form', 'context': self.env.context,
                  'res_model': 'account.move.line',
                  'domain': [('id', 'in', self.with_context(
                      to_date=to_date).stock_fifo_real_time_aml_ids.ids)],
                  'views': [(tree_view_ref.id, 'tree'),
                            (form_view_ref.id, 'form')]}
        return action

    def action_view_stock_moves(self):
        self.ensure_one()
        to_date = self.env.context.get('to_date')
        tree_view_ref = self.env.ref(
            'stock_account.view_move_tree_valuation_at_date')
        form_view_ref = self.env.ref('stock.view_move_form')
        action = {'name': _('Inventory Valuation'),
                  'type': 'ir.actions.act_window', 'view_type': 'form',
                  'view_mode': 'tree,form', 'context': self.env.context,
                  'res_model': 'stock.move',
                  'domain': [('id', 'in', self.with_context(
                      to_date=to_date).stock_fifo_manual_move_ids.ids)],
                  'views': [(tree_view_ref.id, 'tree'),
                            (form_view_ref.id, 'form')]}
        return action
