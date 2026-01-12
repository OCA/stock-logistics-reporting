# Copyright 2022 Tecnativa - Pedro M. Baeza
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestStockPickingReportCustomDescription(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Test customer"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "type": "consu",
            }
        )
        order_form = Form(cls.env["sale.order"])
        order_form.partner_id = cls.customer
        with order_form.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.name = f"{cls.product.display_name}\nCustom description"
        cls.order = order_form.save()

    def test_so_custom_description_transfer_to_picking(self):
        self.order.action_confirm()
        self.assertEqual(
            self.order.order_line.move_ids.description_picking, "Custom description"
        )
        self.order.order_line.name = (
            f"{self.order.order_line.product_id.display_name}\nCustom description 2"
        )
        self.assertEqual(
            self.order.order_line.move_ids.description_picking,
            self.order.order_line.name,
        )
        # Test description_picking no change when update other field than name
        self.order.order_line.price_unit = 42.0
        self.assertEqual(
            self.order.order_line.move_ids.description_picking,
            self.order.order_line.name,
        )
        # Test description_picking when order line name is empty
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.customer
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.name = ""
        order2 = order_form.save()
        order2.action_confirm()
        self.assertEqual(order2.order_line.move_ids.description_picking, "Test product")
        # Test when auto create picking when confirm other doc than SO
        self.env["stock.rule"]._get_stock_move_values(
            product_id=self.product,
            product_qty=1,
            product_uom=self.product.uom_id,
            location_id=self.env.ref("stock.stock_location_customers"),
            name="Test move",
            origin="Test origin",
            company_id=self.env.company,
            values={"date_planned": "2024-01-01 00:00:00"},
        )
