# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import Command

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.stock_picking_operations_multilang.hooks import uninstall_hook


class TestPickingOperationsLanguage(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ja = (
            cls.env["res.lang"]
            .with_context(active_test=False)
            .search([("code", "=", "ja_JP")])
        )
        cls.env["base.language.install"].create({"lang_ids": ja.ids}).lang_install()
        cls.partner.lang = "ja_JP"
        cls.picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.picking_type_in.id,
            }
        )
        cls.warehouse = cls.picking_type_in.warehouse_id
        cls.report = cls.env.ref("stock.action_report_picking")
        cls.product_for_report = cls.env["product.product"].create(
            {"name": "English Product", "is_storable": True}
        )
        cls.product_for_report.with_context(lang="ja_JP").name = "Translated Product"

    def _render_report_html(self, picking):
        with patch(
            "odoo.addons.base.models.ir_actions_report.IrActionsReport.barcode",
            return_value=b"",
        ):
            result = self.report._render_qweb_html(self.report.id, [picking.id])[0]
        return result.decode() if isinstance(result, bytes) else result

    def test_stock_picking_operations_language(self):
        report_html = self._render_report_html(self.picking)
        self.assertIn('lang="ja-JP"', report_html)
        self.assertEqual(self.picking._get_picking_operations_lang(), "ja_JP")

        self.warehouse.picking_operation_language_option = "partner"
        report_html = self._render_report_html(self.picking)
        self.assertIn('lang="ja-JP"', report_html)
        self.assertEqual(self.picking._get_picking_operations_lang(), "ja_JP")

        self.partner.lang = "en_US"
        report_html = self._render_report_html(self.picking)
        self.assertIn("Receipt", report_html)
        self.assertEqual(self.picking._get_picking_operations_lang(), "en_US")

        self.picking.partner_id = False
        report_html = self._render_report_html(self.picking)
        self.assertIn("Receipt", report_html)
        self.assertEqual(self.picking._get_picking_operations_lang(), "en_US")

        self.warehouse.picking_operation_language_option = "warehouse"
        self.warehouse.warehouse_language = "ja_JP"
        report_html = self._render_report_html(self.picking)
        self.assertIn('lang="ja-JP"', report_html)
        self.assertEqual(self.picking._get_picking_operations_lang(), "ja_JP")

        self.warehouse.warehouse_language = "en_US"
        report_html = self._render_report_html(self.picking)
        self.assertIn("Receipt", report_html)
        self.assertEqual(self.picking._get_picking_operations_lang(), "en_US")

    def test_report_uses_translated_field_values(self):
        self.warehouse.picking_operation_language_option = "warehouse"
        self.warehouse.warehouse_language = "ja_JP"
        picking = self.env["stock.picking"].create(
            {
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
                "picking_type_id": self.picking_type_in.id,
                "move_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_for_report.id,
                            "product_uom_id": self.product_for_report.uom_id.id,
                            "location_id": self.supplier_location.id,
                            "location_dest_id": self.stock_location.id,
                            "quantity": 1,
                        }
                    )
                ],
            }
        )

        report_html = self._render_report_html(picking)

        self.assertIn('lang="ja-JP"', report_html)
        self.assertIn("Translated Product", report_html)

    def test_active_lang_count(self):
        """Test computation of active_lang_count"""
        self.assertGreater(self.warehouse.active_lang_count, 0)
        self.assertEqual(
            self.warehouse._lang_get(), self.env["res.lang"].get_installed()
        )

        # Simulate change in warehouse_language
        self.warehouse.warehouse_language = "ja_JP"
        self.warehouse._compute_active_lang_count()

        # Ensure the computed count remains correct
        self.assertEqual(
            self.warehouse.active_lang_count, len(self.env["res.lang"].get_installed())
        )

    def test_uninstall_hook_restores_report_name(self):
        self.report.report_name = (
            "stock_picking_operations_multilang.report_picking_with_language"
        )

        uninstall_hook(self.env)

        self.assertEqual(self.report.report_name, "stock.report_picking")
