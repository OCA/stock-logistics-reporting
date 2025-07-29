from odoo.tests import common


class TestStockPickingSort(common.TransactionCase):
    def setUp(self):
        super().setUp()
        # Prepare the environment for the tests
        uom = self.env.ref("uom.product_uom_unit")

        # Create a product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "uom_id": uom.id,
                "uom_po_id": uom.id,
            }
        )

        # Create a partner
        self.partner = self.env["res.partner"].create({"name": "Client Test"})

        # Create a delivery method
        carrier = self.env["delivery.carrier"].create(
            {
                "name": "Fast Delivery",
                "product_id": self.product.id,
                "delivery_type": "fixed",
                "fixed_price": 10.0,
            }
        )

        # Create a sale order with 3 lines and unordered positions
        SaleOrder = self.env["sale.order"]
        SaleLine = self.env["sale.order.line"]
        self.order1 = SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "carrier_id": carrier.id,
            }
        )
        # Lines with intentionally out-of-order positions
        lines_data1 = [
            {
                "product_id": self.product.id,
                "product_uom_qty": 5,
                "product_uom": uom.id,
                "position": 30,
            },
            {
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "product_uom": uom.id,
                "position": 10,
            },
            {
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "product_uom": uom.id,
                "position": 20,
            },
        ]
        for vals in lines_data1:
            SaleLine.create({"order_id": self.order.id, **vals})

        self.order2 = SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "carrier_id": carrier.id,
            }
        )
        lines_data2 = [
            {
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "product_uom": uom.id,
                "position": 5,
            },
            {
                "product_id": self.product.id,
                "product_uom_qty": 3,
                "product_uom": uom.id,
                "position": 15,
            },
        ]
        for vals in lines_data2:
            SaleLine.create({"order_id": self.order2.id, **vals})

        # Confirmar les dues comandes i assignar quantitats
        self.order1.action_confirm()
        self.order2.action_confirm()
        self.picking1 = self.order1.picking_ids[0]
        self.picking2 = self.order2.picking_ids[0]

        for picking in [self.picking1, self.picking2]:
            for m in picking.move_ids_without_package:
                m.quantity_done = m.product_uom_qty
            picking.button_validate()

    def test_get_sorted_moves_across_orders(self):
        all_moves = (
            self.picking1._get_sorted_moves() + self.picking2._get_sorted_moves()
        )
        positions = [
            (m.sale_line_id.order_id.id, m.sale_line_id.position) for m in all_moves
        ]
        expected = sorted(positions, key=lambda x: x[0] * 1000 + x[1])
        self.assertEqual(
            positions,
            expected,
            "Moves are not sorted by sale_line.position",
        )

    def test_get_sorted_move_lines_across_orders(self):
        all_lines = (
            self.picking1._get_sorted_move_lines()
            + self.picking2._get_sorted_move_lines()
        )
        positions = [
            (ml.move_id.sale_line_id.order_id.id, ml.move_id.sale_line_id.position)
            for ml in all_lines
        ]
        expected = sorted(positions, key=lambda x: x[0] * 1000 + x[1])
        self.assertEqual(
            positions,
            expected,
            "Move lines are not sorted by order_id and then by position",
        )
