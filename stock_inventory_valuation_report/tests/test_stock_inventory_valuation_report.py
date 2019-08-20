# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import datetime
from odoo.tests import common
from odoo.tools import test_reports

_logger = logging.getLogger(__name__)


class TestStockInventoryValuation(common.TransactionCase):

    def setUp(cls):
        super(TestStockInventoryValuation, cls).setUp()

        cls.model = cls._getReportModel()

        cls.qweb_report_name = cls._getQwebReportName()
        cls.xlsx_report_name = cls._getXlsxReportName()
        cls.xlsx_action_name = cls._getXlsxReportActionName()

        cls.report_title = cls._getReportTitle()

        cls.base_filters = cls._getBaseFilters()

        cls.report = cls.model.create(cls.base_filters)
        cls.report._compute_results()

    def test_html(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                self.qweb_report_name,
                                [self.report.id],
                                report_type='qweb-html')

    def test_qweb(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                self.qweb_report_name,
                                [self.report.id],
                                report_type='qweb-pdf')

    def test_xlsx(self):
        test_reports.try_report(self.env.cr, self.env.uid,
                                self.xlsx_report_name,
                                [self.report.id],
                                report_type='xlsx')

    def test_print(self):
        self.report.print_report('qweb')
        self.report.print_report('xlsx')

    def _getReportModel(self):
        return self.env['report.stock.inventory.valuation.report']

    def _getQwebReportName(self):
        return 'stock_inventory_valuation_report.'\
               'report_stock_inventory_valuation_report_pdf'

    def _getXlsxReportName(self):
        return 's_i_v_r.report_stock_inventory_valuation_report_xlsx'

    def _getXlsxReportActionName(self):
        return 'stock_inventory_valuation_report.'\
               'action_stock_inventory_valuation_report_xlsx'

    def _getReportTitle(self):
        return 'Inventory Valuation Report'

    def _getBaseFilters(self):
        return {
            'company_id': self.env.user.company_id.id,
            'compute_at_date': 0,
            'date': datetime.datetime.now(),
            }


class TestStockInventoryValuationReport(common.TransactionCase):

    def setUp(self):
        super(TestStockInventoryValuationReport, self).setUp()
        self.company_id = self.env.ref('base.main_company')
        self.compute_at_date = 0
        self.date = datetime.datetime.now()

    def test_get_report_html(self):
        report = self.env['report.stock.inventory.valuation.report'].create({
            'company_id': self.company_id.id,
            'compute_at_date': self.compute_at_date,
            'date': self.date,
            })
        report._compute_results()
        report.get_html(given_context={
            'active_id': report.id
            })

    def test_wizard(self):
        wizard = self.env['stock.quantity.history'].create({
            'compute_at_date': 0,
            'date': datetime.datetime.now(),
            })
        wizard._export('qweb-pdf')
        wizard.button_export_html()
        wizard.button_export_pdf()
        wizard.button_export_xlsx()
