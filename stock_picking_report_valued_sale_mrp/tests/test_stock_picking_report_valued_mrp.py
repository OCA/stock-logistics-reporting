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
        order_form = Form(cls.env["sale.order"])
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = cls.product_kit
            line_form.product_uom_qty = 5
            line_form.price_unit = 29.9
            line_form.tax_id.clear()
            line_form.tax_id.add(cls.tax10)
        cls.sale_order_3 = order_form.save()
        cls.sale_order_3.action_confirm()
        # Maybe other modules create additional lines in the create
        # method in sale.order model, so let's find the correct line.
        cls.order_line = cls.sale_order_3.order_line.filtered(
            lambda r: r.product_id == cls.product_kit
        )
        cls.order_out_picking = cls.sale_order_3.picking_ids

    def test_01_picking_confirmed(self):
        for line in self.order_out_picking.move_lines:
            line.quantity_done = line.product_uom_qty
        self.order_out_picking.button_validate()
        self.assertAlmostEqual(self.order_out_picking.amount_untaxed, 149.5)
        self.assertAlmostEqual(self.order_out_picking.amount_tax, 14.95)
        self.assertAlmostEqual(self.order_out_picking.amount_total, 164.45)
        # Run the report to detect hidden errors
        self.env.ref("stock.action_report_delivery")._render_qweb_html(
            self.order_out_picking.ids
        )
