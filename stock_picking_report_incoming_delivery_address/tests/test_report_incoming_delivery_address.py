# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo.tests.common import TransactionCase


class TestReportIncomingDeliveryAddress(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].create(
            {
                "name": "Test Warehouse",
                "code": "TEST",
            }
        )
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Product Test 1",
                "type": "product",
            }
        )

    def test_report_incoming_delivery_address(self):
        """Check pickup address is shown in reports (deliveryslip and picking)"""
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.stock_location, 10
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
                            "partner_id": self.partner.id,
                            "product_uom": self.product1.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                            "product_uom_qty": 10,
                            "quantity_done": 4,
                        },
                    ),
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.action_set_quantities_to_reservation()
        picking._action_done()
        return_wizard = (
            self.env["stock.return.picking"]
            .with_context(active_id=picking.id, active_ids=picking.ids)
            .create(
                {
                    "location_id": self.stock_location.id,
                    "picking_id": picking.id,
                }
            )
        )
        return_wizard._onchange_picking_id()
        return_wizard.product_return_moves.quantity = 4
        stock_return_picking_action = return_wizard.create_returns()
        return_pick = self.env["stock.picking"].browse(
            stock_return_picking_action["res_id"]
        )
        # Check pickup address is not shown in reports
        report_pdf_deliveryslip = self.env["ir.actions.report"]._render(
            "stock.action_report_delivery", return_pick.ids
        )
        report_pdf_picking = self.env["ir.actions.report"]._render(
            "stock.action_report_picking", return_pick.ids
        )
        self.assertTrue("Vendor Address:" in str(report_pdf_deliveryslip))
        self.assertTrue("Vendor Address:" in str(report_pdf_picking))
        self.assertFalse("Pick-Up Address:" in str(report_pdf_deliveryslip))
        self.assertFalse("Pick-Up Address:" in str(report_pdf_picking))
        # Check pickup address is shown in reports
        self.warehouse.return_type_id.show_pickup_address = True
        report_pdf_deliveryslip = self.env["ir.actions.report"]._render(
            "stock.action_report_delivery", return_pick.ids
        )
        report_pdf_picking = self.env["ir.actions.report"]._render(
            "stock.action_report_picking", return_pick.ids
        )
        self.assertFalse("Vendor Address:" in str(report_pdf_deliveryslip))
        self.assertFalse("Vendor Address:" in str(report_pdf_picking))
        self.assertTrue("Pick-Up Address:" in str(report_pdf_deliveryslip))
        self.assertTrue("Pick-Up Address:" in str(report_pdf_picking))
