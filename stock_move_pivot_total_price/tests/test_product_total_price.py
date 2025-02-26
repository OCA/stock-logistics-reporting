from datetime import datetime

from odoo.tests.common import TransactionCase


class TestStockPivotTotalPrice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "product", "list_price": 10.0}
        )
        cls.stock_location = cls.env["stock.location"].create(
            {"name": "Location 1", "usage": "internal"}
        )

        cls.stock_location_2 = cls.env["stock.location"].create(
            {"name": "Location 2", "usage": "internal"}
        )

        cls.outgoing_picking_type = cls.env.ref("stock.picking_type_out")

    def create_picking(self, quantity=0):
        picking_data = {
            "picking_type_id": self.outgoing_picking_type.id,
            "move_type": "direct",
            "location_id": self.stock_location.id,
            "location_dest_id": self.stock_location_2.id,
        }
        picking = self.env["stock.picking"].create(picking_data)

        move_data = {
            "picking_id": picking.id,
            "product_id": self.product.id,
            "location_id": self.stock_location.id,
            "location_dest_id": self.stock_location_2.id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date_deadline": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name": self.product.name,
            "product_uom": self.product.uom_id.id,
            "product_uom_qty": quantity,
        }

        move = self.env["stock.move"].create(move_data)
        return picking, move

    def test_total_price_computation(self):
        picking, move = self.create_picking(10.0)
        picking.button_validate()

        move._compute_product_total_price()

        expected_price = self.product.list_price * move.product_uom_qty
        self.assertEqual(move.product_total_price, expected_price)
