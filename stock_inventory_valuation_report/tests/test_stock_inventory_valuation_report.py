# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from dateutil.relativedelta import relativedelta

from odoo.tests import common
from odoo.tools import test_reports


class TestStockInventoryValuation(common.SavepointCase):
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


class TestStockInventoryValuationReport(common.SavepointCase):
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
                "categ_id": self.product_category_all.id,
            }
        )

        partner_id = self.env.ref("base.res_partner_4")
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
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": "Receive product",
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": product_qty,
                            "quantity_done": product_qty,
                        },
                    )
                ],
            }
        )
        receipt.action_confirm()
        receipt.button_validate()
        move = receipt.move_lines
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
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": "Deliver product",
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": product_qty,
                            "quantity_done": product_qty,
                        },
                    )
                ],
            }
        )
        delivery.action_confirm()
        delivery.button_validate()
        date_no_stock = self.date + relativedelta(hours=-6)
        move = delivery.move_lines
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
