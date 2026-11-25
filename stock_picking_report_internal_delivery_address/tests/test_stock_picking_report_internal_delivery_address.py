from unittest.mock import patch

from odoo import Command
from odoo.tools import html2plaintext

from odoo.addons.base.tests.common import BaseCommon


class TestStockPicking(BaseCommon):
    report_xmlids = (
        "stock.action_report_delivery",
        "stock.action_report_picking",
    )

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
        cls.move_partner = cls.env["res.partner"].create(
            {
                "name": "Test Move Partner",
                "street": "456 Unique Move Address ABC",
                "city": "MoveCity",
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Average Ice Cream",
                "type": "consu",
                "is_storable": True,
            }
        )

    def _create_picking(
        self, picking_type_xmlid, *, partner=False, move_partner=False, with_move=True
    ):
        values = {
            "picking_type_id": self.env.ref(picking_type_xmlid).id,
            "partner_id": partner.id if partner else False,
        }
        if with_move:
            values["move_ids"] = [
                Command.create(
                    {
                        "product_id": self.product.id,
                        "product_uom_qty": 1.0,
                        "product_uom": self.product.uom_id.id,
                    }
                )
            ]
        picking = self.env["stock.picking"].create(values)
        if move_partner:
            picking.move_ids[0].partner_id = move_partner
        return picking

    def _render_report_text(self, report_xmlid, picking):
        report_model = self.env["ir.actions.report"]
        with patch.object(type(report_model), "barcode", return_value=b""):
            report_html = report_model._render_qweb_html(report_xmlid, picking.ids)[0]
        return html2plaintext(report_html)

    def _assert_address_in_reports(self, picking, address):
        for report_xmlid in self.report_xmlids:
            with self.subTest(report_xmlid=report_xmlid):
                self.assertIn(
                    address,
                    self._render_report_text(report_xmlid, picking),
                )

    def _assert_delivery_address_hidden(self, picking):
        for report_xmlid in self.report_xmlids:
            with self.subTest(report_xmlid=report_xmlid):
                self.assertNotIn(
                    "Delivery Address",
                    self._render_report_text(report_xmlid, picking),
                )

    def test_internal_picking_address_from_picking_partner(self):
        picking = self._create_picking(
            "stock.picking_type_internal", partner=self.partner
        )

        self.assertTrue(picking.should_print_delivery_address())
        self._assert_address_in_reports(picking, self.partner.street)

    def test_internal_picking_address_from_move_partner(self):
        picking = self._create_picking(
            "stock.picking_type_internal", move_partner=self.move_partner
        )

        self.assertFalse(picking.partner_id)
        self.assertTrue(picking.should_print_delivery_address())
        self._assert_address_in_reports(picking, self.move_partner.street)

    def test_outgoing_picking_keeps_standard_address_behavior(self):
        picking = self._create_picking("stock.picking_type_out", partner=self.partner)

        self.assertTrue(picking.should_print_delivery_address())
        self._assert_address_in_reports(picking, self.partner.street)

    def test_incoming_picking_does_not_show_delivery_address(self):
        picking = self._create_picking("stock.picking_type_in", partner=self.partner)

        self.assertFalse(picking.should_print_delivery_address())
        self._assert_delivery_address_hidden(picking)

    def test_internal_picking_without_partner_hides_delivery_address(self):
        picking = self._create_picking("stock.picking_type_internal")

        self.assertFalse(picking.should_print_delivery_address())
        self._assert_delivery_address_hidden(picking)

    def test_internal_picking_without_moves_does_not_crash(self):
        picking = self._create_picking(
            "stock.picking_type_internal", partner=self.partner, with_move=False
        )

        self.assertFalse(picking.should_print_delivery_address())
        self._assert_delivery_address_hidden(picking)
