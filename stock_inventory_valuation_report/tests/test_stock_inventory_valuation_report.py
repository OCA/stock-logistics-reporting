# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from odoo.tests import common
from odoo.tools import test_reports


class TestStockInventoryValuation(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.model = cls._getReportModel()

        cls.qweb_report_name = cls._getQwebReportName()
        cls.xlsx_report_name = cls._getXlsxReportName()
        cls.xlsx_action_name = cls._getXlsxReportActionName()

        cls.report_title = cls._getReportTitle()

        cls.base_filters = cls._getBaseFilters()

        cls.report = cls.model.create(cls.base_filters)
        cls.report._compute_results()

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

    @classmethod
    def _getReportModel(cls):
        return cls.env["report.stock.inventory.valuation.report"]

    @classmethod
    def _getQwebReportName(cls):
        return (
            "stock_inventory_valuation_report."
            "report_stock_inventory_valuation_report_pdf"
        )

    @classmethod
    def _getXlsxReportName(cls):
        return "s_i_v_r.report_stock_inventory_valuation_report_xlsx"

    @classmethod
    def _getXlsxReportActionName(cls):
        return (
            "stock_inventory_valuation_report."
            "action_stock_inventory_valuation_report_xlsx"
        )

    @classmethod
    def _getReportTitle(cls):
        return "Inventory Valuation Report"

    @classmethod
    def _getBaseFilters(cls):
        return {
            "company_id": cls.env.user.company_id.id,
            "compute_at_date": "0",
            "date": datetime.datetime.now(),
        }


class TestStockInventoryValuationReport(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company_id = cls.env.ref("base.main_company")
        cls.compute_at_date = "0"
        cls.date = datetime.datetime.now()

    def test_get_report_html(self):
        report = self.env["report.stock.inventory.valuation.report"].create(
            {
                "company_id": self.company_id.id,
                "compute_at_date": self.compute_at_date,
                "date": self.date,
            }
        )
        report._compute_results()
        report.get_html(given_context={"active_id": report.id})

    def test_wizard(self):
        wizard = self.env["stock.quantity.history"].create(
            {
                "compute_at_date": "0",
                "inventory_datetime": datetime.datetime.now(),
            }
        )
        wizard._export("qweb-pdf")
        wizard.button_export_html()
        wizard.button_export_pdf()
        wizard.button_export_xlsx()

    def test_date_report_result(self):
        """
        Check that report shows the correct product quantity
        when specifying a date in the past.
        """
        product = self.env["product.product"].create(
            {
                "name": "test valuation report date",
                "type": "product",
                "company_id": self.company_id.id,
                "categ_id": self.env.ref("product.product_category_all").id,
            }
        )

        stock_location_id = self.ref("stock.stock_location_stock")
        partner_id = self.ref("base.res_partner_4")
        product_qty = 50.000
        date_with_stock = datetime.datetime.now()

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
                "company_id": self.company_id.id,
            }
        )
        self.env["stock.move"].create(
            {
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": 50.000,
                "product_uom": product.uom_id.id,
                "picking_id": picking.id,
                "location_id": self.location_2.id,
                "location_dest_id": self.location_1.id,
            }
        )
        picking.action_confirm()
        picking.move_ids_without_package.quantity_done = 50.000
        picking.button_validate()
        self.assertEqual(
            product.with_context(to_date=date_with_stock).quantity_svl, product_qty
        )
        self.assertEqual(product.quantity_svl, product_qty)

        # Report should have a line with the product and its quantity
        report_form = common.Form(self.env["report.stock.inventory.valuation.report"])
        report_form.company_id = self.company_id
        report_form.compute_at_date = "0"
        report = report_form.save()

        # Delivery the product
        product2 = self.env["product.product"].create(
            {
                "name": "test valuation report date2",
                "type": "product",
                "company_id": self.company_id.id,
                "categ_id": self.env.ref("product.product_category_all").id,
            }
        )
        delivery = self.env["stock.picking"].create(
            {
                "location_id": stock_location_id,
                "location_dest_id": self.ref("stock.stock_location_customers"),
                "partner_id": partner_id,
                "picking_type_id": self.ref("stock.picking_type_out"),
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": "Deliver product",
                            "product_id": product2.id,
                            "product_uom": product2.uom_id.id,
                            "product_uom_qty": 5,
                            "quantity_done": 5,
                        },
                    )
                ],
            }
        )
        delivery.action_confirm()
        delivery.button_validate()
        self.assertEqual(
            product2.with_context(to_date=date_with_stock).quantity_svl, -5
        )
        self.assertEqual(product2.quantity_svl, -5)

        # Report should not have a line with the product
        # because it is not available
        report = self.env["report.stock.inventory.valuation.report"].create(
            {
                "company_id": self.company_id.id,
                "compute_at_date": "0",
            }
        )
        product_row = report.results.filtered(lambda r: r.name == product2.name)
        self.assertFalse(product_row)

        # Report computed specifying the date
        # when there was stock should have the product and its quantity
        report = self.env["report.stock.inventory.valuation.report"].create(
            {
                "company_id": self.company_id.id,
                "compute_at_date": "1",
                "date": date_with_stock,
            }
        )
        report._compute_results()
        product_row = report.results.filtered(lambda r: r.name == product2.name)
        self.assertEqual(len(product_row), 1)
        self.assertEqual(product_row.qty_at_date, -5)

    def test_open_table(self):
        """Test retrieving of inventory valuation, when it based on date
        and with different context"""

        # check created action, when inventory valuation depends on date
        quantity_history = self.env["stock.quantity.history"].create(
            {
                "compute_at_date": "1",
                "inventory_datetime": datetime.datetime.now(),
            }
        )
        quantity_action_with_date = quantity_history.open_table()
        self.assertEqual(
            quantity_action_with_date["type"],
            "ir.actions.act_window",
            "type must be 'ir.actions.act_window'",
        )
        self.assertEqual(
            quantity_action_with_date["res_model"],
            "product.product",
            "res_model must be 'product.product'",
        )
        self.assertEqual(
            quantity_action_with_date["domain"],
            "[('type', '=', 'product')]",
            "Bad domain name",
        )

        # check created action, when inventory valuation does not depend on date
        quantity_history.update({"compute_at_date": "0"})
        quantity_action_no_date = quantity_history.open_table()
        self.assertEqual(
            quantity_action_no_date["type"],
            "ir.actions.server",
            "type must be 'ir.actions.server'",
        )
        self.assertEqual(
            quantity_action_no_date["model_name"],
            "stock.quant",
            "model_name must be 'stock.quant'",
        )
