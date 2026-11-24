# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tools import mute_logger

from odoo.addons.printing_auto_base.tests.common import TestPrintingAutoCommon


class TestAutoPrinting(TestPrintingAutoCommon):
    @classmethod
    def setUpReportAndRecord(cls):
        cls.report_ref = "stock.action_report_delivery"
        partner = cls.env["res.partner"].create({"name": "Test partner"})
        product = cls.env["product.product"].create(
            {"name": "Test product", "type": "consu"}
        )
        cls.record = cls.env["stock.picking"].create(
            {
                "partner_id": partner.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": 15.0,
                            "location_id": cls.env.ref("stock.stock_location_stock").id,
                            "location_dest_id": cls.env.ref(
                                "stock.stock_location_customers"
                            ).id,
                        },
                    )
                ],
            }
        )

    def setUp(self):
        # Note: Using setUpClass, cls.record.picking_type_id.auto_printing_ids
        # is reset on each test making them fail
        super().setUp()
        self.printing_auto = self._create_printing_auto_attachment()
        self._create_attachment(self.record, self.data, "1")
        self.record.picking_type_id.auto_printing_ids |= self.printing_auto

    def test_action_done_printing_auto(self):
        self.printing_auto.printer_id = self.printer_1
        self.record._action_done()
        self.assertFalse(self.record.printing_auto_error)

    def test_action_done_printing_error_log(self):
        with mute_logger("odoo.addons.printing_auto_base.models.printing_auto_mixin"):
            self.record._action_done()
        self.assertTrue(self.record.printing_auto_error)

    def test_action_done_printing_error_raise(self):
        self.printing_auto.action_on_error = "raise"
        with self.assertRaises(UserError):
            self.record._action_done()
