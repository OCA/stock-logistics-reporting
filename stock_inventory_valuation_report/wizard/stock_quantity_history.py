# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'stock_inventory_valuation_report.'
            'action_stock_inventory_valuation_report_html')
        vals = action.read()[0]
        context1 = vals.get('context', {})
        if isinstance(context1, pycompat.string_types):
            context1 = safe_eval(context1)
        model = self.env['report.stock.inventory.valuation.report']
        report = model.create(self._prepare_stock_inventory_valuation_report())
        context1['active_id'] = report.id
        context1['active_ids'] = report.ids
        vals['context'] = context1
        return vals

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    def _prepare_stock_inventory_valuation_report(self):
        self.ensure_one()
        return {
            'company_id': self.env.user.company_id.id,
            'compute_at_date': self.compute_at_date,
            'date': self.date,
        }

    def _export(self, report_type):
        model = self.env['report.stock.inventory.valuation.report']
        report = model.create(self._prepare_stock_inventory_valuation_report())
        return report.print_report(report_type)
