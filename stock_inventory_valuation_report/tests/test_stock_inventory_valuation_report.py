# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import Command, fields
from odoo.exceptions import AccessError
from odoo.tests import common, new_test_user
from odoo.tools import mute_logger, test_reports

from odoo.addons.stock_account.tests.common import TestStockValuationCommon


class TestStockInventoryValuationOutputs(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.report = cls.env["report.stock.inventory.valuation.report"].create(
            {"company_id": cls.env.company.id}
        )

    def test_html(self):
        test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "stock_inventory_valuation_report."
            "report_stock_inventory_valuation_report_pdf",
            [self.report.id],
            report_type="qweb-html",
        )

    def test_qweb_pdf(self):
        test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "stock_inventory_valuation_report."
            "report_stock_inventory_valuation_report_pdf",
            [self.report.id],
            report_type="qweb-pdf",
        )

    @mute_logger("odoo.tools.test_reports")
    def test_xlsx(self):
        test_reports.try_report(
            self.env.cr,
            self.env.uid,
            "s_i_v_r.report_stock_inventory_valuation_report_xlsx",
            [self.report.id],
            report_type="xlsx",
        )

    def test_print_actions(self):
        self.assertEqual(self.report.print_report("qweb")["report_type"], "qweb-pdf")
        self.assertEqual(self.report.print_report("xlsx")["report_type"], "xlsx")


class TestStockInventoryValuationReport(TestStockValuationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.now = fields.Datetime.now()

    def _create_product(self, name, category=None, standard_price=10.0):
        return self.env["product.product"].create(
            {
                "name": name,
                "is_storable": True,
                "categ_id": (category or self.category_standard).id,
                "standard_price": standard_price,
            }
        )

    def _get_report(
        self,
        *,
        company=None,
        inventory_datetime=None,
        product=None,
        product_tmpl=None,
        extra_context=None,
    ):
        company = company or self.company
        context = {
            **self.env.context,
            "allowed_company_ids": company.ids,
            **(extra_context or {}),
        }
        if product:
            context["product_id"] = product.id
        if product_tmpl:
            context["product_tmpl_id"] = product_tmpl.id
        return (
            self.env["report.stock.inventory.valuation.report"]
            .with_context(**context)
            .with_company(company)
            .create(
                {
                    "company_id": company.id,
                    "inventory_datetime": inventory_datetime or fields.Datetime.now(),
                }
            )
        )

    def _get_product_line(self, report, product):
        return report.results.filtered(lambda line: line.name == product.name)

    def test_get_report_html(self):
        report = self._get_report()
        result = report.get_html(given_context={"active_id": report.id})
        self.assertIn("Inventory Valuation Report", result["html"])
        self.assertEqual(
            self.env["report.stock.inventory.valuation.report"]
            .with_context(active_id=False)
            ._get_html(),
            {},
        )

    @mute_logger("odoo.tools.test_reports")
    def test_populated_xlsx(self):
        product = self._create_product("XLSX product", standard_price=10)
        self._make_in_move(product, 2, unit_cost=10)
        report = self._get_report(product=product)
        report_action = self.env.ref(
            "stock_inventory_valuation_report."
            "action_stock_inventory_valuation_report_xlsx"
        )

        content, output_format = report_action._render_xlsx(
            report_action.report_name, report.ids, data={}
        )

        self.assertEqual(output_format, "xlsx")
        self.assertTrue(content.startswith(b"PK"))
        self.assertEqual(report.results.stock_value, 20)

    def test_wizard_actions_and_active_company(self):
        wizard = self.env["stock.quantity.history"].create({})
        values = wizard._prepare_stock_inventory_valuation_report()
        self.assertEqual(values["company_id"], self.env.company.id)
        self.assertEqual(wizard._export("qweb-pdf")["report_type"], "qweb-pdf")
        self.assertEqual(wizard.button_export_pdf()["report_type"], "qweb-pdf")
        self.assertEqual(wizard.button_export_xlsx()["report_type"], "xlsx")
        html_action = wizard.button_export_html()
        self.assertIn("active_id", html_action["context"])

        action = self.env.ref(
            "stock_inventory_valuation_report."
            "action_stock_inventory_valuation_report_html"
        )
        with patch.object(type(action), "read", return_value=[{"context": {}}]):
            html_action = wizard.button_export_html()
        self.assertIn("active_id", html_action["context"])

        other_wizard = (
            self.env["stock.quantity.history"]
            .with_company(self.other_company)
            .with_context(allowed_company_ids=self.other_company.ids)
            .create({})
        )
        self.assertEqual(
            other_wizard._prepare_stock_inventory_valuation_report()["company_id"],
            self.other_company.id,
        )

    def test_wizard_preserves_inventory_datetime(self):
        inventory_datetime = self.now - relativedelta(days=7)
        wizard = self.env["stock.quantity.history"].create(
            {"inventory_datetime": inventory_datetime}
        )
        self.assertEqual(
            wizard._prepare_stock_inventory_valuation_report()["inventory_datetime"],
            inventory_datetime,
        )
        wizard.inventory_datetime = False
        self.assertNotIn(
            "inventory_datetime",
            wizard._prepare_stock_inventory_valuation_report(),
        )

    @mute_logger(
        "odoo.addons.stock_inventory_valuation_report.wizard.stock_quantity_history"
    )
    def test_wizard_handles_serialized_action_context(self):
        wizard = self.env["stock.quantity.history"].create({})
        action = self.env.ref(
            "stock_inventory_valuation_report."
            "action_stock_inventory_valuation_report_html"
        )
        original_context = action.context
        try:
            action.context = "{'test_key': 'test_value'}"
            result = wizard.button_export_html()
            self.assertEqual(result["context"]["test_key"], "test_value")

            action.context = "invalid python code {"
            result = wizard.button_export_html()
            self.assertIn("active_id", result["context"])
        finally:
            action.context = original_context

    def test_historical_quantity_and_cost(self):
        product = self._create_product(
            "Historical AVCO product", category=self.category_avco
        )
        date_1 = self.now - relativedelta(days=3)
        date_2 = self.now - relativedelta(days=2)
        between_dates = self.now - relativedelta(days=2, hours=12)

        with freeze_time(date_1):
            self._make_in_move(product, 10, unit_cost=10)
        with freeze_time(date_2):
            self._make_in_move(product, 10, unit_cost=20)

        first_report = self._get_report(
            product=product, inventory_datetime=between_dates
        )
        first_line = self._get_product_line(first_report, product)
        self.assertEqual(first_line.qty_at_date, 10)
        self.assertEqual(first_line.standard_price, 10)
        self.assertEqual(first_line.stock_value, 100)

        current_report = self._get_report(product=product)
        current_line = self._get_product_line(current_report, product)
        self.assertEqual(current_line.qty_at_date, 20)
        self.assertEqual(current_line.standard_price, 15)
        self.assertEqual(current_line.stock_value, 300)

    def test_cost_methods(self):
        cases = (
            ("standard", self.category_standard, 10.0),
            ("average", self.category_avco, 15.0),
            ("fifo", self.category_fifo, 15.0),
        )
        for name, category, expected_cost in cases:
            with self.subTest(cost_method=name):
                product = self._create_product(
                    f"{name} valuation product", category=category
                )
                self._make_in_move(product, 5, unit_cost=10)
                self._make_in_move(product, 5, unit_cost=20)
                line = self._get_product_line(
                    self._get_report(product=product), product
                )
                self.assertEqual(line.qty_at_date, 10)
                self.assertEqual(line.standard_price, expected_cost)
                self.assertEqual(line.stock_value, 10 * expected_cost)

    def test_alternate_move_uom_uses_product_uom(self):
        product = self._create_product("Pack receipt product")
        move = self._make_in_move(
            product,
            2,
            unit_cost=10,
            uom_id=self.uom_pack_of_6.id,
        )
        self.assertEqual(move.move_line_ids.quantity, 2)
        self.assertEqual(move.move_line_ids.quantity_product_uom, 12)

        line = self._get_product_line(self._get_report(product=product), product)
        self.assertEqual(line.qty_at_date, 12)
        self.assertEqual(line.uom_id, product.uom_id)

    def test_company_isolation_and_cost(self):
        product = self._create_product("Shared multi-company product")
        product.company_id = False
        product.with_company(self.company).standard_price = 10
        product.with_company(self.other_company).standard_price = 40
        self._make_in_move(product, 2, company=self.company, unit_cost=10)
        self._make_in_move(product, 3, company=self.other_company, unit_cost=40)

        company_report = self._get_report(company=self.company, product=product)
        company_line = self._get_product_line(company_report, product)
        self.assertEqual(company_report.company_id, self.company)
        self.assertEqual(company_line.qty_at_date, 2)
        self.assertEqual(company_line.standard_price, 10)

        other_report = self._get_report(company=self.other_company, product=product)
        other_line = self._get_product_line(other_report, product)
        self.assertEqual(other_report.company_id, self.other_company)
        self.assertEqual(other_line.qty_at_date, 3)
        self.assertEqual(other_line.standard_price, 40)
        self.assertEqual(other_line.currency_id, self.other_company.currency_id)

    def test_consigned_quantity_is_included(self):
        product = self._create_product("Consigned product")
        self._make_in_move(product, 3, unit_cost=10, owner_id=self.owner.id)
        line = self._get_product_line(self._get_report(product=product), product)
        self.assertEqual(line.qty_at_date, 3)

    def test_internal_transfer_does_not_change_total(self):
        product = self._create_product("Internal transfer product")
        self._make_in_move(product, 10, unit_cost=10)
        other_location = self.env["stock.location"].create(
            {
                "name": "Secondary internal location",
                "usage": "internal",
                "location_id": self.warehouse.view_location_id.id,
                "company_id": self.company.id,
            }
        )
        self._make_out_move(
            product,
            4,
            location_dest_id=other_location.id,
            force_assign=True,
        )
        line = self._get_product_line(self._get_report(product=product), product)
        self.assertEqual(line.qty_at_date, 10)

    def test_inventory_scrap_and_return_directions(self):
        product = self._create_product("Direction product")
        self._make_in_move(
            product,
            10,
            unit_cost=10,
            location_id=self.inventory_location.id,
        )
        self._make_out_move(
            product,
            4,
            location_dest_id=self.inventory_location.id,
        )
        self._make_in_move(
            product,
            2,
            unit_cost=10,
            location_id=self.customer_location.id,
        )
        line = self._get_product_line(self._get_report(product=product), product)
        self.assertEqual(line.qty_at_date, 8)

    def test_zero_and_negative_stock_are_excluded(self):
        zero_product = self._create_product("Zero stock product")
        self._make_in_move(zero_product, 5, unit_cost=10)
        self._make_out_move(zero_product, 5)
        self.assertFalse(
            self._get_product_line(self._get_report(product=zero_product), zero_product)
        )

        negative_product = self._create_product("Negative stock product")
        self._make_out_move(negative_product, 2)
        self.assertFalse(
            self._get_product_line(
                self._get_report(product=negative_product), negative_product
            )
        )

    def test_product_and_template_filters_with_product_precedence(self):
        product_a = self._create_product("Filtered product A")
        product_b = self._create_product("Filtered product B")
        self._make_in_move(product_a, 1, unit_cost=10)
        self._make_in_move(product_b, 2, unit_cost=10)

        product_report = self._get_report(
            product=product_a,
            product_tmpl=product_b.product_tmpl_id,
        )
        self.assertEqual(product_report.results.mapped("name"), [product_a.name])

        template_report = self._get_report(product_tmpl=product_b.product_tmpl_id)
        self.assertEqual(template_report.results.mapped("name"), [product_b.name])

    def test_non_storable_product_is_excluded(self):
        product = self.env["product.product"].create(
            {"name": "Service product", "is_storable": False}
        )
        report = self._get_report(product=product)
        self.assertFalse(report.results)

    def test_user_without_stock_group_is_denied(self):
        user = new_test_user(
            self.env,
            login="inventory_valuation_no_stock_access",
            groups="base.group_user",
            company_id=self.company.id,
            company_ids=[Command.set(self.company.ids)],
        )
        with self.assertRaises(AccessError):
            self.env["report.stock.inventory.valuation.report"].with_user(user).create(
                {
                    "company_id": self.company.id,
                    "inventory_datetime": self.now,
                }
            )

    def test_cutoff_after_delivery_excludes_product(self):
        product = self._create_product("Delivered product")
        receipt_date = self.now - relativedelta(days=2)
        delivery_date = self.now - relativedelta(days=1)
        with freeze_time(receipt_date):
            self._make_in_move(product, 5, unit_cost=10)
        with freeze_time(delivery_date):
            self._make_out_move(product, 5)

        before_delivery = self._get_report(
            product=product,
            inventory_datetime=receipt_date + datetime.timedelta(hours=1),
        )
        self.assertEqual(
            self._get_product_line(before_delivery, product).qty_at_date, 5
        )
        self.assertFalse(
            self._get_product_line(self._get_report(product=product), product)
        )
