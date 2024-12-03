# Copyright 2022 Tecnativa - Pedro M. Baeza
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestStockPickingReportCustomDescription(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Test customer"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "type": "product",
                "description_sale": "Custom description",
            }
        )
        order_form = common.Form(cls.env["sale.order"])
        order_form.partner_id = cls.customer
        with order_form.order_line.new() as line_form:
            line_form.product_id = cls.product
        cls.order = order_form.save()

    def test_so_custom_description_transfer_to_picking(self):
        self.order.action_confirm()
        self.assertEqual(
            self.order.order_line.move_ids.description_picking, "Custom description"
        )
        self.order.order_line.name = "Custom description 2"
        self.assertEqual(
            self.order.order_line.move_ids.description_picking,
            self.order.order_line.name,
        )
