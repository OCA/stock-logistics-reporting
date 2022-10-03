# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import time
from datetime import date

from odoo.tests import common
from odoo.tools import test_reports

_logger = logging.getLogger(__name__)


class TestStockCard(common.TransactionCase):
    def setUp(self):
        super().setUp()

        # Create uom:
        uom_id = self.ref("uom.product_uom_unit")

        # Create products:
        self.product_A = self.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "uom_id": uom_id,
                "uom_po_id": uom_id,
            }
        )

        # Create location:
        self.location_1 = self.env.ref("stock.stock_location_stock")
        self.location_2 = self.env.ref("stock.stock_location_customers")

        # Create operation type:
        operation_type = self.env.ref("stock.picking_type_in")

        # Create stock picking:
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.location_2.id,
                "location_dest_id": self.location_1.id,
                "picking_type_id": operation_type.id,
            }
        )
        self.env["stock.move"].create(
            {
                "name": self.product_A.name,
                "product_id": self.product_A.id,
                "product_uom_qty": 50.000,
                "product_uom": self.product_A.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.location_2.id,
                "location_dest_id": self.location_1.id,
            }
        )
        picking.action_confirm()
        picking.move_ids_without_package.quantity_done = 50.000
        picking.button_validate()

        self.model = self._getReportModel()

        self.qweb_report_name = self._getQwebReportName()
        self.xlsx_report_name = self._getXlsxReportName()
        self.xlsx_action_name = self._getXlsxReportActionName()

        self.report_title = self._getReportTitle()

        self.base_filters = self._getBaseFilters()

        self.report = self.model.create(self.base_filters)
        self.report._compute_results()

    def test_html(self):
        test_reports.try_report(
            self.env.cr,
            self.env.uid,
            self.qweb_report_name,
            [self.report.id],
            report_type="qweb-html",
        )

    def test_qweb(self):
        test_reports.try_report(
            self.env.cr,
            self.env.uid,
            self.qweb_report_name,
            [self.report.id],
            report_type="qweb-pdf",
        )

    def test_xlsx(self):
        test_reports.try_report(
            self.env.cr,
            self.env.uid,
            self.xlsx_report_name,
            [self.report.id],
            report_type="xlsx",
        )

    def test_print(self):
        self.report.print_report("qweb")
        self.report.print_report("xlsx")

    def _getReportModel(self):
        return self.env["report.stock.card.report"]

    def _getQwebReportName(self):
        return "stock_card_report.report_stock_card_report_pdf"

    def _getXlsxReportName(self):
        return "stock_card_report.report_stock_card_report_xlsx"

    def _getXlsxReportActionName(self):
        return "stock_card_report.action_report_stock_card_report_xlsx"

    def _getReportTitle(self):
        return "Stock Card Report"

    def _getBaseFilters(self):
        return {
            "product_ids": [(6, 0, [self.product_A.id])],
            "location_id": self.location_1.id,
        }


class TestStockCardReport(common.TransactionCase):
    def setUp(self):
        super().setUp()

        # Create uom:
        uom_id = self.ref("uom.product_uom_unit")

        # Create products:
        self.product_A = self.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "uom_id": uom_id,
                "uom_po_id": uom_id,
            }
        )
        self.product_B = self.env["product.product"].create(
            {
                "name": "Product B",
                "type": "product",
                "uom_id": uom_id,
                "uom_po_id": uom_id,
            }
        )

        # Create location:
        self.location_1 = self.env.ref("stock.stock_location_stock")
        self.location_2 = self.env.ref("stock.stock_location_customers")

        # Create operation type:
        operation_type = self.env.ref("stock.picking_type_in")

        # Create stock picking:
        picking_1 = self.env["stock.picking"].create(
            {
                "location_id": self.location_2.id,
                "location_dest_id": self.location_1.id,
                "picking_type_id": operation_type.id,
            }
        )
        self.env["stock.move"].create(
            {
                "name": self.product_A.name,
                "product_id": self.product_A.id,
                "product_uom_qty": 50.000,
                "product_uom": self.product_A.uom_id.id,
                "picking_id": picking_1.id,
                "location_id": self.location_2.id,
                "location_dest_id": self.location_1.id,
            }
        )
        picking_1.action_confirm()
        picking_1.move_ids_without_package.quantity_done = 50.000
        picking_1.button_validate()

        picking_2 = self.env["stock.picking"].create(
            {
                "location_id": self.location_2.id,
                "location_dest_id": self.location_1.id,
                "picking_type_id": operation_type.id,
            }
        )
        self.env["stock.move"].create(
            {
                "name": self.product_B.name,
                "product_id": self.product_B.id,
                "product_uom_qty": 100.000,
                "product_uom": self.product_B.uom_id.id,
                "picking_id": picking_2.id,
                "location_id": self.location_2.id,
                "location_dest_id": self.location_1.id,
            }
        )
        picking_2.action_confirm()
        picking_2.move_ids_without_package.quantity_done = 100.000
        picking_2.button_validate()

    def test_reports(self):
        report = self.env["report.stock.card.report"].create(
            {
                "product_ids": [(6, 0, [self.product_A.id, self.product_B.id])],
                "location_id": self.location_1.id,
            }
        )
        report._compute_results()
        report.print_report("qweb")
        report.print_report("xlsx")

    def test_get_report_html(self):
        report = self.env["report.stock.card.report"].create(
            {
                "product_ids": [(6, 0, [self.product_A.id, self.product_B.id])],
                "location_id": self.location_1.id,
            }
        )
        report._compute_results()
        report.get_html(given_context={"active_id": report.id})

    def test_wizard_date_range(self):
        date_range = self.env["date.range"]
        self.type = self.env["date.range.type"].create(
            {"name": "Month", "company_id": False, "allow_overlap": False}
        )
        dt = date_range.create(
            {
                "name": "FiscalYear",
                "date_start": time.strftime("%Y-%m-01"),
                "date_end": time.strftime("%Y-%m-28"),
                "type_id": self.type.id,
            }
        )
        wizard = self.env["stock.card.report.wizard"].create(
            {
                "date_range_id": dt.id,
                "date_from": time.strftime("%Y-%m-28"),
                "date_to": time.strftime("%Y-%m-01"),
                "product_ids": [(6, 0, [self.product_A.id, self.product_B.id])],
                "location_id": self.location_1.id,
            }
        )
        wizard._onchange_date_range_id()
        self.assertEqual(
            wizard.date_from, date(date.today().year, date.today().month, 1)
        )
        self.assertEqual(
            wizard.date_to, date(date.today().year, date.today().month, 28)
        )
        wizard._export("qweb-pdf")
        wizard.button_export_html()
        wizard.button_export_pdf()
        wizard.button_export_xlsx()
