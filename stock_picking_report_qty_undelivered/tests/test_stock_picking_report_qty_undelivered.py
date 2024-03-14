# Copyright 2024 Moduon Team S.L.
# License GPL-3.0 (https://www.gnu.org/licenses/gpl-3.0)


from odoo.tests.common import TransactionCase


class TestReportQtyUndelivered(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Product Test 1",
                "type": "product",
            }
        )
        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Product Test 2",
                "type": "product",
            }
        )
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")

    def test_report_qty_not_delivered(self):
        """Test delivery"""
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.stock_location, 10
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product2, self.stock_location, 10
        )
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": self.picking_type_out.id,
                "move_ids_without_package": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Move Product 1",
                            "product_id": self.product1.id,
                            "product_uom": self.product1.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                            "product_uom_qty": 10,
                            "quantity_done": 4,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Test Move Product 2",
                            "product_id": self.product2.id,
                            "product_uom": self.product1.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                            "product_uom_qty": 10,
                            "quantity_done": 10,
                        },
                    ),
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.with_context(
            skip_backorder=True, picking_ids_not_to_backorder=picking.ids
        ).button_validate()
        report_pdf = self.env["ir.actions.report"]._render(
            "stock.action_report_delivery", picking.ids
        )
        self.assertFalse("Summary of undelivered quantities:" in str(report_pdf))
        self.picking_type_out.summary_qty_undelivered = True
        report_pdf = self.env["ir.actions.report"]._render(
            "stock.action_report_delivery", picking.ids
        )
        self.assertTrue("Summary of undelivered quantities:" in str(report_pdf))
        self.assertTrue(
            "Product Test 1"
            in str(report_pdf).split("Summary of undelivered quantities:")[1]
        )
        self.assertFalse(
            "Product Test 2"
            in str(report_pdf).split("Summary of undelivered quantities:")[1]
        )
