# Copyright 2020 Tecnativa - David Vidal
from odoo.tests import Form

from odoo.addons.stock_picking_report_valued.tests.test_stock_picking_valued import (
    TestStockPickingValued,
)


class TestStockPickingValuedMrp(TestStockPickingValued):
    @classmethod
    def setUpClass(cls):
        """We want to run parent class tests again to ensure everything
        works as expected even if no kits are present"""
        super().setUpClass()
        cls.res_partner = cls.env["res.partner"]
        cls.product_product = cls.env["product.product"]
        cls.product_kit = cls.product_product.create(
            {"name": "Product test 1", "type": "consu"}
        )
        cls.product_kit_comp_1 = cls.product_product.create(
            {"name": "Product Component 1", "type": "product"}
        )
        cls.product_kit_comp_2 = cls.product_product.create(
            {"name": "Product Component 2", "type": "product"}
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_id": cls.product_kit.id,
                "product_tmpl_id": cls.product_kit.product_tmpl_id.id,
                "type": "phantom",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {"product_id": cls.product_kit_comp_1.id, "product_qty": 2},
                    ),
                    (
                        0,
                        0,
                        {"product_id": cls.product_kit_comp_2.id, "product_qty": 4},
                    ),
                ],
            }
        )
        cls.product_2 = cls.product_product.create(
            {"name": "Product test 2", "type": "product"}
        )
        (
            cls.sale_order_3,
            cls.order_line,
            cls.order_out_picking,
        ) = cls._create_sale_order_with_lines(
            cls,
            product=cls.product_kit,
            quantity=5,
            price_unit=29.9,
            tax=cls.tax10,
        )

    def _create_sale_order_with_lines(self, product, quantity, price_unit, tax=None):
        """Create a sale order with a single line, confirm it, and return
        the sale order, filtered order line, and picking."""
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = product
            line_form.product_uom_qty = quantity
            line_form.price_unit = price_unit
            line_form.tax_id.clear()
            if tax:
                line_form.tax_id.add(tax)
        sale_order = order_form.save()
        sale_order.action_confirm()
        order_line = sale_order.order_line.filtered(lambda r: r.product_id == product)
        picking = sale_order.picking_ids[0] if sale_order.picking_ids else None
        return sale_order, order_line, picking

    def test_01_picking_confirmed(self):
        for line in self.order_out_picking.move_ids:
            line.quantity_done = line.product_uom_qty
        self.order_out_picking.button_validate()
        self.assertAlmostEqual(self.order_out_picking.amount_untaxed, 149.5)
        self.assertAlmostEqual(self.order_out_picking.amount_tax, 14.95)
        self.assertAlmostEqual(self.order_out_picking.amount_total, 164.45)
        # Run the report to detect hidden errors
        self.env["ir.actions.report"]._render_qweb_html(
            self.env.ref("stock.action_report_delivery"), self.order_out_picking.ids
        )

    def _create_sale_order_for_kits(self, qty):
        """Create a new sale order for the configured kit product."""
        return self._create_sale_order_with_lines(
            product=self.product_kit,
            quantity=qty,
            price_unit=29.9,
        )

    def test_02_get_components_per_kit_return_redelivery(self):
        """Component-per-kit ratio is correct after full return + redelivery."""
        sale, so_line, picking = self._create_sale_order_for_kits(qty=2)
        picking = picking[0]
        # First delivery
        picking.action_assign()
        for line in picking.move_ids:
            line.quantity_done = line.product_uom_qty
        picking.button_validate()
        # Return delivery
        return_wizard_form = Form(
            self.env["stock.return.picking"].with_context(
                active_id=picking.id,
                active_model="stock.picking",
            )
        )
        return_wiz = return_wizard_form.save()
        res = return_wiz.create_returns()["res_id"]
        return_picking = self.env["stock.picking"].browse(res)
        return_picking.action_assign()
        for line in return_picking.move_ids:
            line.quantity_done = line.product_uom_qty
        return_picking.button_validate()
        # Redelivery
        sale._action_cancel()
        sale.action_draft()
        sale.action_confirm()
        redelivery = sale.picking_ids.filtered(
            lambda p: p.state not in ("done", "cancel")
        )
        self.assertTrue(redelivery)
        redelivery = redelivery[0]
        redelivery.action_assign()
        for line in redelivery.move_ids:
            line.quantity_done = line.product_uom_qty
        redelivery.button_validate()
        # Validate component ratios
        kit_lines = redelivery.move_line_ids.filtered("phantom_product_id")
        self.assertTrue(kit_lines)
        expected_per_kit = {
            self.product_kit_comp_1.id: 2.0,
            self.product_kit_comp_2.id: 4.0,
        }
        for sale_line in kit_lines.mapped("sale_line"):
            move_lines = kit_lines.filtered(lambda x: x.sale_line == sale_line)
            phantom_line = move_lines[:1]
            if not phantom_line:
                continue
            move = phantom_line.move_id
            expected = expected_per_kit[move.product_id.id]
            got = move._get_components_per_kit()
            self.assertEqual(
                got,
                expected,
                f"_get_components_per_kit returned {got} but expected {expected} "
                f"for component {move.product_id.display_name}",
            )
