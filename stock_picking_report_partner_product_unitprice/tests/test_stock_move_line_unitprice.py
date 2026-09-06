# Copyright 2026 NICO SOLUTIIONS - ENGERINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo.addons.base.tests.common import BaseCommon


class TestStockMoveLineUnitPrice(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
            }
        )
        cls.currency = cls.env.ref("base.USD")
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test Pricelist",
                "currency_id": cls.currency.id,
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "pricelist_id": cls.pricelist.id,
            }
        )
        cls.sale_line = cls.env["sale.order.line"].create(
            {
                "order_id": cls.sale_order.id,
                "product_id": cls.product.id,
                "price_unit": 42.0,
            }
        )
        cls.move = cls.env["stock.move"].create(
            {
                "product_id": cls.product.id,
                "sale_line_id": cls.sale_line.id,
                "product_uom_qty": 1,
                "product_uom": cls.product.uom_id.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
            }
        )
        cls.move_line = cls.env["stock.move.line"].create(
            {
                "move_id": cls.move.id,
                "product_id": cls.product.id,
                "location_id": cls.move.location_id.id,
                "location_dest_id": cls.move.location_dest_id.id,
                "quantity": 1,
            }
        )
        cls.move_no_sale = cls.env["stock.move"].create(
            {
                "product_id": cls.product.id,
                "product_uom_qty": 1,
                "product_uom": cls.product.uom_id.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
            }
        )
        cls.move_line_no_sale = cls.env["stock.move.line"].create(
            {
                "move_id": cls.move_no_sale.id,
                "product_id": cls.product.id,
                "location_id": cls.move_no_sale.location_id.id,
                "location_dest_id": cls.move_no_sale.location_dest_id.id,
            }
        )

    def test_aggregated_quantities_unit_price(self):
        """Test that unit_price and currency_id are correctly set if sale_line exists"""
        result = self.move_line._get_aggregated_product_quantities()
        self.assertTrue(result)
        line = list(result.values())[0]
        self.assertIn("unit_price", line)
        self.assertEqual(line["unit_price"], 42.0)
        self.assertIn("currency_id", line)
        self.assertEqual(line["currency_id"].id, self.sale_line.currency_id.id)

    def test_aggregated_quantities_no_sale_line(self):
        """Test that unit_price and currency_id are NOT set if no sale_line exists"""
        result = self.move_line_no_sale._get_aggregated_product_quantities()
        self.assertTrue(result)
        line = list(result.values())[0]
        self.assertNotIn("unit_price", line)
        self.assertNotIn("currency_id", line)

    def test_aggregation_separates_different_prices(self):
        sale_line_2 = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.id,
                "price_unit": 99.0,
            }
        )
        move_2 = self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "sale_line_id": sale_line_2.id,
                "product_uom_qty": 1,
                "product_uom": self.product.uom_id.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            }
        )
        move_line_2 = self.env["stock.move.line"].create(
            {
                "move_id": move_2.id,
                "product_id": self.product.id,
                "location_id": move_2.location_id.id,
                "location_dest_id": move_2.location_dest_id.id,
            }
        )
        result = (self.move_line | move_line_2)._get_aggregated_product_quantities()
        self.assertEqual(len(result), 2)
        prices = sorted(line["unit_price"] for line in result.values())
        self.assertEqual(prices, [42.0, 99.0])

    def test_same_price_is_aggregated(self):
        sale_line_2 = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.id,
                "price_unit": 42.0,
            }
        )
        move_2 = self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "sale_line_id": sale_line_2.id,
                "product_uom_qty": 1,
                "product_uom": self.product.uom_id.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            }
        )
        move_line_2 = self.env["stock.move.line"].create(
            {
                "move_id": move_2.id,
                "product_id": self.product.id,
                "quantity": 1,
                "location_id": move_2.location_id.id,
                "location_dest_id": move_2.location_dest_id.id,
            }
        )
        result = (self.move_line | move_line_2)._get_aggregated_product_quantities()
        self.assertEqual(len(result), 1)
        line = list(result.values())[0]
        self.assertEqual(line["quantity"], 2)
