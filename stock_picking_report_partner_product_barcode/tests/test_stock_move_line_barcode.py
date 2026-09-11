# Copyright 2026 NICO SOLUTIIONS - ENGERINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from unittest.mock import patch

from odoo.addons.base.tests.common import BaseCommon


class TestStockMoveLineBarcode(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "barcode": "1234567890123",
                "tracking": "lot",
            }
        )
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
            }
        )
        cls.move = cls.env["stock.move"].create(
            {
                "product_id": cls.product.id,
                "product_uom_qty": 1,
                "product_uom": cls.product.uom_id.id,
                "picking_id": cls.picking.id,
                "location_id": cls.picking.location_id.id,
                "location_dest_id": cls.picking.location_dest_id.id,
            }
        )
        cls.move_line = cls.env["stock.move.line"].create(
            {
                "move_id": cls.move.id,
                "picking_id": cls.picking.id,
                "product_id": cls.product.id,
                "location_id": cls.move.location_id.id,
                "location_dest_id": cls.move.location_dest_id.id,
                "quantity": 1,
            }
        )

    def test_barcode_in_aggregated_quantities(self):
        result = self.move_line._get_aggregated_product_quantities()
        self.assertTrue(result, "Aggregated result should not be empty")
        line = list(result.values())[0]
        self.assertIn("barcode", line, "Barcode key must exist in aggregated line")
        self.assertEqual(
            line["barcode"], "1234567890123", "Barcode value should match the product"
        )

    def test_aggregated_quantities_without_product(self):
        aggregated = {"test": {"product": False}}

        class FakeSuper:
            def _get_aggregated_product_quantities(self, **kwargs):
                return aggregated

        with patch(
            "odoo.addons.stock_picking_report_partner_product_barcode.models.stock_move_line.super",
            return_value=FakeSuper(),
        ):
            result = self.move_line._get_aggregated_product_quantities()

        self.assertFalse(result["test"]["product"])
        self.assertNotIn("barcode", result["test"])

    def test_barcode_in_serial_move_line(self):
        lot = self.env["stock.lot"].create(
            {
                "name": "LOT-001",
                "product_id": self.product.id,
            }
        )
        move_line = self.env["stock.move.line"].create(
            {
                "move_id": self.move.id,
                "picking_id": self.picking.id,
                "product_id": self.product.id,
                "lot_id": lot.id,
                "location_id": self.move.location_id.id,
                "location_dest_id": self.move.location_dest_id.id,
                "quantity": 1,
            }
        )
        html = self.env["ir.qweb"]._render(
            "stock.stock_report_delivery_has_serial_move_line",
            {
                "move_line": move_line,
                "has_multi_level_packages": False,
                "has_serial_number": True,
                "render_barcode": True,
                "format_number": lambda value: str(value),
            },
        )
        html = html.decode() if isinstance(html, bytes) else html
        self.assertIn(
            'name="move_line_lot_barcode"',
            html,
        )
