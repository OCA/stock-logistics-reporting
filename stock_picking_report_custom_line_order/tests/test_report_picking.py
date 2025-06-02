# Copyright 2025 Foodles (https://www.foodles.co/).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.tests import tagged
from odoo.tests.common import SavepointCase


@tagged("post_install", "-at_install")
class TestReportPicking(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        [cls.product_a, cls.product_b, cls.product_c] = cls.env[
            "product.product"
        ].create(
            [
                {
                    "name": name,
                    "type": "product",
                    "company_id": cls.env.company.id,
                }
                for name in ["Product A", "Product B", "Product C"]
            ]
        )
        cls.location_stock = cls.env.ref("stock.stock_location_stock")
        [cls.location_stock_a, cls.location_stock_b] = cls.env["stock.location"].create(
            [
                {
                    "name": name,
                    "location_id": cls.location_stock.id,
                    "usage": "internal",
                    "company_id": cls.env.company.id,
                }
                for name in ["Stock A", "Stock B"]
            ]
        )
        cls.env["stock.quant"].create(
            [
                {
                    "product_id": cls.product_a.id,
                    "location_id": cls.location_stock_a.id,
                    "quantity": 1,
                },
                {
                    "product_id": cls.product_a.id,
                    "location_id": cls.location_stock_b.id,
                    "quantity": 2,
                },
                {
                    "product_id": cls.product_b.id,
                    "location_id": cls.location_stock_a.id,
                    "quantity": 4,
                },
                {
                    "product_id": cls.product_c.id,
                    "location_id": cls.location_stock_b.id,
                    "quantity": 8,
                },
            ]
        )
        cls.picking_type_out = cls.env["stock.picking.type"].create(
            {
                "name": "Test Picking Type Out",
                "code": "outgoing",
                "sequence_code": "TEST_OUT",
                "warehouse_id": cls.env.ref("stock.warehouse0").id,
            }
        )
        cls.picking = cls.env["stock.picking"].create(
            [
                {
                    "picking_type_id": cls.picking_type_out.id,
                    "location_id": cls.location_stock.id,
                    "location_dest_id": cls.env.ref(
                        "stock.stock_location_customers"
                    ).id,
                    "scheduled_date": "2025-01-01 12:00:00",
                    "move_lines": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.id,
                                "product_uom_qty": 8,
                                "name": product.name,
                                "product_uom": product.uom_id.id,
                            },
                        )
                        for product in cls.product_a | cls.product_b | cls.product_c
                    ],
                },
            ]
        )
        [
            cls.move_product_a,
            cls.move_product_b,
            cls.move_product_c,
        ] = cls.picking.move_ids_without_package

    def setUp(self):
        super().setUp()
        self.picking.action_confirm()
        self.picking.action_assign()

    def test_get_moves_for_report_picking(self):
        self.assertEqual(
            self.picking.get_moves_for_report_picking(),
            self.move_product_a | self.move_product_b | self.move_product_c,
        )

    def test_get_move_lines_for_report_picking(self):
        move_line_product_a_location_a = self.move_product_a.move_line_ids.filtered(
            lambda ml: ml.location_id.id == self.location_stock_a.id
        )
        self.assertEqual(len(move_line_product_a_location_a), 1)

        move_line_product_a_location_b = self.move_product_a.move_line_ids.filtered(
            lambda ml: ml.location_id.id == self.location_stock_b.id
        )
        self.assertEqual(len(move_line_product_a_location_b), 1)

        self.assertEqual(
            self.move_product_a.get_move_lines_for_report_picking(),
            move_line_product_a_location_a | move_line_product_a_location_b,
        )
