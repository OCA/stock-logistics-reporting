# Copyright (C) 2022 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.addons.base.tests.common import BaseCommon


class TestModule(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PickingReportWizard = cls.env["picking.summary.wizard"]
        cls.StockPicking = cls.env["stock.picking"]
        cls.outPickingType = cls.env.ref("stock.picking_type_out")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.ir_actions_report = cls.env["ir.actions.report"]
        cls.report_name = "stock_picking_report_summary.report_picking_summary"

        cls.partner_1 = cls.env["res.partner"].create({"name": "Picking Partner 1"})
        cls.partner_2 = cls.env["res.partner"].create({"name": "Picking Partner 2"})
        cls.product_category = cls.env["product.category"].create(
            {"name": "Summary Category"}
        )
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Summary Product A",
                "categ_id": cls.product_category.id,
                "standard_price": 4.0,
                "uom_id": cls.uom_unit.id,
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Summary Product B",
                "categ_id": cls.product_category.id,
                "standard_price": 2.0,
                "uom_id": cls.uom_unit.id,
                "uom_ids": [Command.link(cls.uom_dozen.id)],
            }
        )
        cls.product_without_category = cls.env["product.product"].create(
            {
                "name": "Summary Product Without Category",
                "categ_id": False,
                "standard_price": 1.0,
                "uom_id": cls.uom_unit.id,
            }
        )
        cls.picking_1 = cls._create_picking(
            cls.partner_1,
            [
                Command.create(cls._move_vals(cls.product_a, 3.0)),
                Command.create(cls._move_vals(cls.product_b, 0.0)),
            ],
        )
        cls.picking_2 = cls._create_picking(
            cls.partner_2,
            [
                Command.create(cls._move_vals(cls.product_a, 2.0)),
                Command.create(
                    cls._move_vals(cls.product_b, 2.0, product_uom=cls.uom_dozen)
                ),
                Command.create(cls._move_vals(cls.product_without_category, 1.0)),
            ],
        )

    @classmethod
    def _move_vals(cls, product, quantity, product_uom=None):
        product_uom = product_uom or product.uom_id
        return {
            "product_id": product.id,
            "product_uom_qty": quantity,
            "product_uom": product_uom.id,
            "location_id": cls.stock_location.id,
            "location_dest_id": cls.customer_location.id,
        }

    @classmethod
    def _create_picking(cls, partner, move_commands):
        return cls.StockPicking.create(
            {
                "partner_id": partner.id,
                "picking_type_id": cls.outPickingType.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.customer_location.id,
                "move_ids": move_commands,
            }
        )

    def _create_wizard(self, **values):
        return self.PickingReportWizard.with_context(
            active_model="stock.picking",
            active_ids=(self.picking_1 | self.picking_2).ids,
        ).create(values)

    def _render_wizard(self, wizard):
        html = self.ir_actions_report._render_qweb_html(self.report_name, wizard.ids)[0]
        return html.decode() if isinstance(html, bytes) else html

    def test_wizard_summary_lines(self):
        wizard = self._create_wizard()

        self.assertEqual(wizard.picking_line_qty, 2)
        self.assertEqual(
            wizard.picking_line_ids.mapped("picking_id"),
            self.picking_1 | self.picking_2,
        )

        product_lines = {
            line.product_id: line.quantity_total for line in wizard.product_line_ids
        }
        self.assertEqual(product_lines[self.product_a], 5.0)
        self.assertEqual(product_lines[self.product_b], 24.0)
        self.assertEqual(product_lines[self.product_without_category], 1.0)

        sum_th = sum(wizard.mapped("product_line_ids.standard_price_total"))
        wizard._compute_standard_price_total()
        self.assertEqual(sum_th, wizard.standard_price_total)
        self.assertEqual(wizard.standard_price_total, 69.0)

    def test_report_render_options(self):
        custom_note = "Picking summary custom note"
        self.picking_1.note = custom_note
        wizard = self._create_wizard(print_prices=True)

        html = self._render_wizard(wizard)

        self.assertIn("Products Summary", html)
        self.assertIn("Pickings Details", html)
        self.assertIn(custom_note, html)
        self.assertIn("Standard Unit", html)
        self.assertIn("Standard Price Total", html)
        self.assertIn("Summary Product A", html)
        self.assertIn("Summary Product B", html)
        self.assertIn("Summary Product Without Category", html)
        self.assertIn("color:gray;", html)

    def test_report_render_without_optional_sections(self):
        wizard = self._create_wizard(
            print_summary=False,
            print_unit_in_list=False,
            print_prices=False,
        )

        html = self._render_wizard(wizard)

        self.assertNotIn("Products Summary", html)
        self.assertIn("Pickings Details", html)
        self.assertNotIn("Standard Unit", html)
