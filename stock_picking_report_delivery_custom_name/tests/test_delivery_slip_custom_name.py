# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from odoo.tests import Form, common
from odoo.tools import html2plaintext


class TestStockPickingReportCustomName(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Super secret part name",
                "default_code": "SPN",
                "type": "consu",
                "description_pickingout": "Generic part public name",
            }
        )
        cls.delivery_type = cls.env.ref("stock.picking_type_out")
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = cls.env.ref("stock.picking_type_out")
        with picking_form.move_ids_without_package.new() as move_form:
            move_form.product_id = cls.product
            move_form.quantity_done = 1
        cls.picking = picking_form.save()

    def _get_report_in_plain_text(self):
        html, _ = self.env["ir.actions.report"]._render_qweb_html(
            "stock.action_report_delivery", self.picking.ids
        )
        return html2plaintext(html)

    def test_delivery_slip_with_public_name(self):
        text = self._get_report_in_plain_text()
        self.assertTrue("Generic part public name" in text)
        self.assertFalse("Super secret part name" in text)
        self.picking.button_validate()
        # Now we're seeing detailed operations
        text = self._get_report_in_plain_text()
        self.assertTrue("Generic part public name" in text)
        self.assertFalse("Super secret part name" in text)

    def test_delivery_slip_with_regular_name(self):
        self.picking.move_ids.description_picking = False
        text = self._get_report_in_plain_text()
        self.assertFalse("Generic part public name" in text)
        self.assertTrue("[SPN] Super secret part name" in text)
        # The description is ignored as it's equal to the product name
        self.picking.move_ids.description_picking = "Super secret part name"
        text = self._get_report_in_plain_text()
        self.assertFalse("Generic part public name" in text)
        self.assertTrue("[SPN] Super secret part name" in text)
        self.assertEqual(
            1,
            text.count("Super secret part name"),
            "The name should be printed just once!",
        )
