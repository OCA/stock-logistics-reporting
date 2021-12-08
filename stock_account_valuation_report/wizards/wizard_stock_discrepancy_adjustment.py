# Copyright 2021 ForgeFlow S.L.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizardStockDiscrepancyAdjustment(models.TransientModel):

    _name = 'wizard.stock.discrepancy.adjustment'
    _description = 'Wizard Stock Discrepancy Adjustment'

    def _get_default_stock_journal(self):
        return self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', self.env.user.company_id.id)
        ], limit=1)

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        domain=[('type', '=', 'general')],
        default=_get_default_stock_journal
    )
    increase_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Increase account',
        domain=[("deprecated", "=", False)],
        required=False
    )
    decrease_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Decrease account',
        domain=[("deprecated", "=", False)],
        required=False
    )
    to_date = fields.Date(
        string='To date',
        required=True,
        default=fields.Date.today(),
    )
    product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Product',
    )

    @api.onchange(
        'to_date'
    )
    def _onchange_at_date(self):
        product_model = self.env['product.product']
        if self.to_date:
            products = product_model.with_context(to_date=self.to_date).search([
                ('valuation_discrepancy', '!=', 0.0)
            ])
            self.product_ids = products.ids or [(6, 0, [])]

    def action_create_adjustment(self):
        move_model = self.env['account.move']
        move_line_model = self.env['account.move.line']
        product_model = self.env['product.product']
        moves_created = move_model.browse()
        if self.product_ids:
            products_with_discrepancy = products = \
                product_model.with_context(to_date=self.to_date).browse(self.product_ids.ids)
            for product in products_with_discrepancy:
                move_data = {
                    'journal_id': self.journal_id.id,
                    'date': self.to_date,
                    'ref': _('Adjust for Stock Valuation Discrepancy')
                }
                valuation_account = product.product_tmpl_id._get_product_accounts()['stock_valuation']
                if not valuation_account:
                    raise UserError(_("Product %s doesn't have stock valuation account assigned") % (product.display_name))
                move_data['line_ids'] = [(0, 0, {
                    'account_id': valuation_account.id,
                    'product_id': product.id,
                    'quantity': product.qty_discrepancy,
                    'credit': product.valuation_discrepancy < 0 and abs(product.valuation_discrepancy) or 0.0,
                    'debit': product.valuation_discrepancy > 0 and product.valuation_discrepancy or 0.0,
                }), (0, 0, {
                    'account_id':
                        product.valuation_discrepancy < 0
                        and self.increase_account_id.id or self.decrease_account_id.id,
                    'product_id': product.id,
                    'quantity': product.qty_discrepancy,
                    'credit': product.valuation_discrepancy > 0 and product.valuation_discrepancy or 0.0,
                    'debit': product.valuation_discrepancy < 0 and abs(product.valuation_discrepancy) or 0.0,
                })]
                move = move_model.create(move_data)
                move.action_post()
                moves_created |= move
            action = self.env.ref('account.action_move_journal_line').read()[0]
            action['domain'] = [('id', 'in', moves_created.ids)]
            return action
        return {'type': 'ir.actions.act_window_close'}

