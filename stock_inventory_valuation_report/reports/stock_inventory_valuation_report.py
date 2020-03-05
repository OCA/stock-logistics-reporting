# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockInventoryValuationView(models.TransientModel):
    _name = 'stock.inventory.valuation.view'
    _description = 'Stock Inventory Valuation View'

    name = fields.Char()
    reference = fields.Char()
    barcode = fields.Char()
    qty_at_date = fields.Float()
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
    )
    cost_currency_id = fields.Many2one(
        comodel_name='res.currency',
    )
    standard_price = fields.Float()
    stock_value = fields.Float()
    cost_method = fields.Char()


class StockInventoryValuationReport(models.TransientModel):
    _name = 'report.stock.inventory.valuation.report'
    _description = 'Stock Inventory Valuation Report'

    # Filters fields, used for data computation
    company_id = fields.Many2one(
        comodel_name='res.company',
    )
    compute_at_date = fields.Integer()
    date = fields.Datetime()

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name='stock.inventory.valuation.view',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )

    @api.multi
    def _compute_results(self):
        self.ensure_one()
        if not self.compute_at_date:
            self.date = fields.Datetime.now()
        products = self.env['product.product'].\
            search([('type', '=', 'product'), ('qty_available', '!=', 0)]).\
            with_context(dict(to_date=self.date, company_owned=True,
                              create=False, edit=False))
        ReportLine = self.env['stock.inventory.valuation.view']
        for product in products:
            standard_price = product.standard_price
            if self.date:
                standard_price = product.get_history_price(
                    self.env.user.company_id.id,
                    date=self.date)
            line = {
                'name': product.name,
                'reference': product.default_code,
                'barcode': product.barcode,
                'qty_at_date': product.qty_at_date,
                'uom_id': product.uom_id,
                'currency_id': product.currency_id,
                'cost_currency_id': product.cost_currency_id,
                'standard_price': standard_price,
                'stock_value': product.qty_at_date * standard_price,
                'cost_method': product.cost_method,
            }
            if product.qty_at_date != 0:
                self.results += ReportLine.new(line)

    @api.multi
    def print_report(self, report_type='qweb'):
        self.ensure_one()
        action = report_type == 'xlsx' and self.env.ref(
            'stock_inventory_valuation_report.'
            'action_stock_inventory_valuation_report_xlsx') or \
            self.env.ref('stock_inventory_valuation_report.'
                         'action_stock_inventory_valuation_report_pdf')
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'stock_inventory_valuation_report.'
                'report_stock_inventory_valuation_report_html').render(
                    rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()
