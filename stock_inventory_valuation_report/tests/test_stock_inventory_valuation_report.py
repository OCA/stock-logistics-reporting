# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import datetime

from dateutil.relativedelta import relativedelta

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

    def test_date_report_result(self):
        """
        Check that report shows the correct product quantity
        when specifying a date in the past.
        """
        product = self.env['product.product'].create({
            'name': 'test valuation report date',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
        })
        stock_location_id = self.ref('stock.stock_location_stock')
        partner_id = self.ref('base.res_partner_4')
        product_qty = 100
        date_with_stock = datetime.datetime.now() + relativedelta(days=-1)

        # Receive the product
        receipt = self.env['stock.picking'].create({
            'location_id': self.ref('stock.stock_location_suppliers'),
            'location_dest_id': stock_location_id,
            'partner_id': partner_id,
            'picking_type_id': self.ref('stock.picking_type_in'),
            'move_lines': [(0, 0, {
                'name': 'Receive product',
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_uom_qty': product_qty,
                'quantity_done': product_qty,
            })]
        })
        receipt.action_confirm()
        receipt.action_done()
        receipt.move_lines.date = date_with_stock
        self.assertEqual(
            product.with_context(to_date=date_with_stock).qty_available,
            product_qty)
        self.assertEqual(product.qty_available, product_qty)

        # Report should have a line with the product and its quantity
        report = self.env['report.stock.inventory.valuation.report'].create({
            'company_id': self.company_id.id,
            'compute_at_date': 0,
            })
        product_row = report.results.filtered(lambda r: r.name == product.name)
        self.assertEqual(len(product_row), 1)
        self.assertEqual(product_row.qty_at_date, product_qty)

        # Delivery the product
        delivery = self.env['stock.picking'].create({
            'location_id':  stock_location_id,
            'location_dest_id': self.ref('stock.stock_location_customers'),
            'partner_id': partner_id,
            'picking_type_id': self.ref('stock.picking_type_out'),
            'move_lines': [(0, 0, {
                'name': 'Deliver product',
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_uom_qty': product_qty,
                'quantity_done': product_qty,
            })]
        })
        delivery.action_confirm()
        delivery.action_done()
        self.assertEqual(
            product.with_context(to_date=date_with_stock).qty_available,
            product_qty)
        self.assertEqual(product.qty_available, 0)

        # Report should not have a line with the product
        # because it is not available
        report = self.env['report.stock.inventory.valuation.report'].create({
            'company_id': self.company_id.id,
            'compute_at_date': 0,
            })
        product_row = report.results.filtered(lambda r: r.name == product.name)
        self.assertFalse(product_row)

        # Report computed specifying the date
        # when there was stock should have the product and its quantity
        report = self.env['report.stock.inventory.valuation.report'].create({
            'company_id': self.company_id.id,
            'compute_at_date': 1,
            'date': date_with_stock,
        })
        product_row = report.results.filtered(lambda r: r.name == product.name)
        self.assertEqual(len(product_row), 1)
        self.assertEqual(product_row.qty_at_date, product_qty)
