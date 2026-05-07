# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from dateutil.relativedelta import relativedelta

from odoo.tests import common
from odoo.tools import mute_logger, test_reports


class TestStockInventoryValuation(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.inv_valuation_report_model = cls.env[
            "report.stock.inventory.valuation.report"
        ]

        cls.qweb_report_name = (
            "stock_inventory_valuation_report."
            "report_stock_inventory_valuation_report_pdf"
        )
        cls.xlsx_report_name = "s_i_v_r.report_stock_inventory_valuation_report_xlsx"
        cls.xlsx_action_name = (
            "stock_inventory_valuation_report."
            "action_stock_inventory_valuation_report_xlsx"
        )

        cls.report_title = "Inventory Valuation Report"

        cls.base_filters = {
            "company_id": cls.env.user.company_id.id,
        }

        cls.report = cls.inv_valuation_report_model.create(cls.base_filters)

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

    @mute_logger("odoo.tools.test_reports")
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


class TestStockInventoryValuationReport(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company_id = cls.env.ref("base.main_company")
        cls.date = datetime.datetime.now()

        cls.location_stock_id = cls.env.ref("stock.stock_location_stock")
        cls.location_customers_id = cls.env.ref("stock.stock_location_customers")
        cls.location_suppliers_id = cls.env.ref("stock.stock_location_suppliers")

        cls.picking_type_in_id = cls.env.ref("stock.picking_type_in")
        cls.picking_type_out_id = cls.env.ref("stock.picking_type_out")
        cls.product_category_all = cls.env.ref("product.product_category_all")

    def test_get_report_html(self):
        report = self.env["report.stock.inventory.valuation.report"].create(
            {
                "company_id": self.company_id.id,
                "inventory_datetime": self.date,
            }
        )
        report._compute_results()
        report.get_html(given_context={"active_id": report.id})

    def test_wizard(self):
        wizard = self.env["stock.quantity.history"].create({})
        wizard._export("qweb-pdf")
        wizard.button_export_html()
        wizard.button_export_pdf()
        wizard.button_export_xlsx()

    def test_wizard_with_inventory_datetime(self):
        """
        Test wizard with inventory_datetime set
        to cover line 49 where inventory_datetime is checked.
        """
        inventory_datetime = datetime.datetime.now() + relativedelta(days=-7)
        wizard = self.env["stock.quantity.history"].create(
            {"inventory_datetime": inventory_datetime}
        )

        # Test _prepare_stock_inventory_valuation_report with datetime
        vals = wizard._prepare_stock_inventory_valuation_report()
        self.assertEqual(
            vals["inventory_datetime"],
            inventory_datetime,
            msg="inventory_datetime should be included in prepared values",
        )

        # Test export methods with datetime
        wizard._export("qweb-pdf")
        result = wizard.button_export_html()
        self.assertIn(
            "context", result, msg="HTML export should return action with context"
        )

    @mute_logger(
        "odoo.addons.stock_inventory_valuation_report.wizard.stock_quantity_history"
    )
    def test_wizard_button_export_html_with_string_context(self):
        """
        Test button_export_html when action context is a string
        to cover lines 22-29 including the safe_eval exception handling.
        """
        wizard = self.env["stock.quantity.history"].create({})

        # Mock the action to have a string context (normal case)
        action = self.env.ref(
            "stock_inventory_valuation_report."
            "action_stock_inventory_valuation_report_html"
        )

        # Store original context
        original_context = action.context

        try:
            # Test with valid string context
            action.context = "{'test_key': 'test_value'}"
            result = wizard.button_export_html()
            self.assertIsInstance(
                result, dict, msg="button_export_html should return a dict"
            )
            self.assertIn("context", result, msg="Result should contain context")

            # Test with invalid string context to trigger exception (lines 22-26)
            action.context = "invalid python code {"
            result = wizard.button_export_html()
            # Should handle exception gracefully and return empty context
            self.assertIsInstance(
                result, dict, msg="Should return dict even with invalid context"
            )

        finally:
            # Restore original context
            action.context = original_context

    def test_wizard_export_methods_coverage(self):
        """
        Test all export methods to ensure full coverage
        of wizard functionality.
        """
        inventory_datetime = datetime.datetime.now()
        wizard = self.env["stock.quantity.history"].create(
            {"inventory_datetime": inventory_datetime}
        )

        # Test PDF export
        pdf_result = wizard.button_export_pdf()
        self.assertTrue(pdf_result, msg="PDF export should return a result")

        # Test XLSX export
        xlsx_result = wizard.button_export_xlsx()
        self.assertTrue(xlsx_result, msg="XLSX export should return a result")

        # Test HTML export
        html_result = wizard.button_export_html()
        self.assertIsInstance(html_result, dict, msg="HTML export should return a dict")
        self.assertIn("context", html_result, msg="HTML result should have context")
        # Verify that active_id and active_ids are in context (line 29)
        context = html_result.get("context", {})
        if isinstance(context, dict):
            self.assertIn(
                "active_id",
                context,
                msg="Context should contain active_id after update",
            )

    def test_date_report_result(self):
        """
        Check that report shows the correct product quantity
        when specifying a date in the past.
        """
        product = self.env["product.product"].create(
            {
                "name": "test valuation report date",
                "type": "consu",
                "is_storable": True,
                "company_id": self.company_id.id,
                "categ_id": self.product_category_all.id,
            }
        )

        partner_id = self.env["res.partner"].create({"name": "Test Partner"})
        product_qty = 100
        date_with_stock = self.date + relativedelta(days=-1)

        # Receive the product
        receipt = self.env["stock.picking"].create(
            {
                "location_id": self.location_suppliers_id.id,
                "location_dest_id": self.location_stock_id.id,
                "picking_type_id": self.picking_type_in_id.id,
                "partner_id": partner_id.id,
                "company_id": self.company_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Receive product",
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": product_qty,
                        },
                    )
                ],
            }
        )
        receipt.action_confirm()
        for move_line in receipt.move_line_ids:
            move_line.quantity = product_qty
        receipt.button_validate()
        move = receipt.move_ids
        move.date = date_with_stock
        move.stock_valuation_layer_ids._write({"create_date": date_with_stock})
        self.assertEqual(
            product.with_context(to_date=date_with_stock).quantity_svl,
            product_qty,
            msg="Product should be present in stock at this date",
        )
        self.assertEqual(
            product.quantity_svl,
            product_qty,
            msg="Product should be present in stock at this date",
        )

        # Report should have a line with the product and its quantity
        report = self.env["report.stock.inventory.valuation.report"].create(
            {
                "company_id": self.company_id.id,
            }
        )
        product_row = report.results.filtered(lambda r: r.name == product.name)
        self.assertEqual(
            len(product_row),
            1,
            msg="There should be one line for this produce in the report",
        )
        self.assertEqual(
            product_row.qty_at_date,
            product_qty,
            msg="The product should have full quantity",
        )

        # Deliver the product
        delivery = self.env["stock.picking"].create(
            {
                "location_id": self.location_stock_id.id,
                "location_dest_id": self.location_customers_id.id,
                "partner_id": partner_id.id,
                "company_id": self.company_id.id,
                "picking_type_id": self.picking_type_out_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Deliver product",
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": product_qty,
                        },
                    )
                ],
            }
        )
        delivery.action_confirm()
        for move_line in delivery.move_line_ids:
            move_line.quantity = product_qty
        delivery.button_validate()
        date_no_stock = self.date + relativedelta(hours=-6)
        move = delivery.move_ids
        move.date = date_no_stock
        move.stock_valuation_layer_ids._write({"create_date": date_no_stock})
        self.assertEqual(
            product.with_context(to_date=date_with_stock).quantity_svl,
            product_qty,
            msg="The product should have full quantity at this date.",
        )
        self.assertEqual(
            product.with_context(to_date=self.date).quantity_svl,
            0,
            msg="The product should not be present at this date.",
        )

        report = self.env["report.stock.inventory.valuation.report"].create(
            {
                "company_id": self.company_id.id,
                "inventory_datetime": date_no_stock,
            }
        )
        product_row = report.results.filtered(lambda r: r.name == product.name)
        self.assertFalse(
            product_row,
            msg="Product should not be present in this report "
            "for this date, because it was delivered.",
        )

        report = self.env["report.stock.inventory.valuation.report"].create(
            {
                "company_id": self.company_id.id,
                "inventory_datetime": date_with_stock,
            }
        )
        product_row = report.results.filtered(lambda r: r.name == product.name)
        self.assertEqual(
            len(product_row),
            1,
            msg="Report for this date should have one line for the product.",
        )
        self.assertEqual(
            product_row.qty_at_date,
            product_qty,
            msg="Report for this date should show full quantity for the product",
        )

    def test_report_with_product_id_context(self):
        """
        Test report generation with product_id in context
        to cover the product_id filtering branch.
        """
        product = self.env["product.product"].create(
            {
                "name": "test product_id filter",
                "type": "consu",
                "is_storable": True,
                "company_id": self.company_id.id,
                "categ_id": self.product_category_all.id,
            }
        )

        # Create stock movement for the product
        partner_id = self.env["res.partner"].create({"name": "Test Partner"})
        receipt = self.env["stock.picking"].create(
            {
                "location_id": self.location_suppliers_id.id,
                "location_dest_id": self.location_stock_id.id,
                "picking_type_id": self.picking_type_in_id.id,
                "partner_id": partner_id.id,
                "company_id": self.company_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Receive product",
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": 50,
                        },
                    )
                ],
            }
        )
        receipt.action_confirm()
        for move_line in receipt.move_line_ids:
            move_line.quantity = 50
        receipt.button_validate()

        # Generate report with product_id in context
        report = (
            self.env["report.stock.inventory.valuation.report"]
            .with_context(product_id=product.id)
            .create(
                {
                    "company_id": self.company_id.id,
                }
            )
        )

        # Should have exactly one line for this product
        self.assertEqual(
            len(report.results),
            1,
            msg="Report should have exactly one line when filtered by product_id",
        )
        self.assertEqual(
            report.results[0].name,
            product.name,
            msg="Report line should be for the filtered product",
        )

    def test_report_with_product_tmpl_id_context(self):
        """
        Test report generation with product_tmpl_id in context
        to cover the product_tmpl_id filtering branch.
        """
        product = self.env["product.product"].create(
            {
                "name": "test product_tmpl_id filter",
                "type": "consu",
                "is_storable": True,
                "company_id": self.company_id.id,
                "categ_id": self.product_category_all.id,
            }
        )

        # Create stock movement for the product
        partner_id = self.env["res.partner"].create({"name": "Test Partner"})
        receipt = self.env["stock.picking"].create(
            {
                "location_id": self.location_suppliers_id.id,
                "location_dest_id": self.location_stock_id.id,
                "picking_type_id": self.picking_type_in_id.id,
                "partner_id": partner_id.id,
                "company_id": self.company_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Receive product",
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": 30,
                        },
                    )
                ],
            }
        )
        receipt.action_confirm()
        for move_line in receipt.move_line_ids:
            move_line.quantity = 30
        receipt.button_validate()

        # Generate report with product_tmpl_id in context
        report = (
            self.env["report.stock.inventory.valuation.report"]
            .with_context(product_tmpl_id=product.product_tmpl_id.id)
            .create(
                {
                    "company_id": self.company_id.id,
                }
            )
        )

        # Should have exactly one line for products of this template
        product_row = report.results.filtered(lambda r: r.name == product.name)
        self.assertEqual(
            len(product_row),
            1,
            msg="Report should have line for product with filtered template",
        )

    def test_report_with_no_storable_products(self):
        """
        Test report generation when no storable products exist
        to cover the early return branch when products list is empty.
        """
        # Create a non-storable product
        product = self.env["product.product"].create(
            {
                "name": "test non-storable product",
                "type": "service",
                "company_id": self.company_id.id,
                "categ_id": self.product_category_all.id,
            }
        )

        # Generate report with this non-storable product in context
        report = (
            self.env["report.stock.inventory.valuation.report"]
            .with_context(product_id=product.id)
            .create(
                {
                    "company_id": self.company_id.id,
                }
            )
        )

        # Should have no results since the product is not storable
        self.assertEqual(
            len(report.results),
            0,
            msg="Report should have no results for non-storable products",
        )
