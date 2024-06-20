# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestPickingOperationsLanguage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ja = (
            cls.env["res.lang"]
            .with_context(active_test=False)
            .search([("code", "=", "ja_JP")])
        )
        cls.env["base.language.install"].create({"lang_ids": ja.ids}).lang_install()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test Partner", "lang": "ja_JP"}
        )
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.picking_type_in.id,
            }
        )
        cls.warehouse = cls.picking_type_in.warehouse_id
        cls.report = cls.env.ref("stock.action_report_picking")

    def test_stock_picking_operations_language(self):
        report_result = self.report._render_qweb_pdf(self.report.id, [self.picking.id])
        self.assertIn('lang="en-US"', str(report_result[0]))

        self.warehouse.picking_operation_language_option = "partner"
        report_result = self.report._render_qweb_pdf(self.report.id, [self.picking.id])
        self.assertIn('lang="ja-JP"', str(report_result[0]))

        self.partner.lang = "en_US"
        report_result = self.report._render_qweb_pdf(self.report.id, [self.picking.id])
        self.assertIn('lang="en-US"', str(report_result[0]))

        self.picking.partner_id = False
        report_result = self.report._render_qweb_pdf(self.report.id, [self.picking.id])
        self.assertIn('lang="en-US"', str(report_result[0]))

        self.warehouse.picking_operation_language_option = "warehouse"
        self.warehouse.warehouse_language = "ja_JP"
        report_result = self.report._render_qweb_pdf(self.report.id, [self.picking.id])
        self.assertIn('lang="ja-JP"', str(report_result[0]))

        self.warehouse.warehouse_language = "en_US"
        report_result = self.report._render_qweb_pdf(self.report.id, [self.picking.id])
        self.assertIn('lang="en-US"', str(report_result[0]))
