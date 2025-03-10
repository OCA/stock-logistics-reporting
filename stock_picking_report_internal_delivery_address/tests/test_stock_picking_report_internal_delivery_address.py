from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestStockPicking(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "street": "123 Unique Test Address XYZ",
                "city": "TestCity",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Average Ice Cream",
                "is_storable": True,
            }
        )
        cls.internal_picking = cls.env["stock.picking"].create(
            {
                "name": "Test Internal Picking",
                "picking_type_id": cls.env.ref("stock.picking_type_internal").id,
                "partner_id": cls.partner.id,
                "move_ids_without_package": [
                    Command.create(
                        {
                            "name": "Test Move Internal",
                            "product_id": cls.product.id,
                            "product_uom_qty": 1.0,
                            "product_uom": cls.product.uom_id.id,
                        },
                    )
                ],
            }
        )
        cls.outgoing_picking = cls.env["stock.picking"].create(
            {
                "name": "Test Outgoing Picking",
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "partner_id": cls.partner.id,
                "move_ids_without_package": [
                    Command.create(
                        {
                            "name": "Test Move Outgoing",
                            "product_id": cls.product.id,
                            "product_uom_qty": 1.0,
                            "product_uom": cls.product.uom_id.id,
                        },
                    )
                ],
            }
        )

    def test_delivery_address_shown_in_internal_report(self):
        """Test that delivery address is shown in internal picking delivery slip"""
        # Generate delivery slip report HTML for internal picking
        report_html = self.env["ir.actions.report"]._render_qweb_html(
            "stock.report_deliveryslip", self.internal_picking.id
        )[0]
        if isinstance(report_html, bytes):
            report_html = report_html.decode("utf-8")
        unique_address = "123 Unique Test Address XYZ"
        self.assertIn(
            unique_address,
            report_html,
            "The delivery address should be printed on the internal "
            "picking delivery slip.",
        )

    def test_delivery_address_shown_in_outgoing_report(self):
        """Test that delivery address is shown in outgoing picking delivery slip"""
        report_html = self.env["ir.actions.report"]._render_qweb_html(
            "stock.report_deliveryslip", self.outgoing_picking.id
        )[0]
        if isinstance(report_html, bytes):
            report_html = report_html.decode("utf-8")
        unique_address = "123 Unique Test Address XYZ"
        self.assertIn(
            unique_address,
            report_html,
            "The delivery address should be printed on the outgoing picking "
            "delivery slip.",
        )
