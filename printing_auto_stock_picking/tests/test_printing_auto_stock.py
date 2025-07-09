# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tools import mute_logger

from odoo.addons.printing_auto_base.tests.common import (
    TestPrintingAutoCommon,
    patch_print_document,
)


@patch_print_document()
class TestAutoPrinting(TestPrintingAutoCommon):
    @classmethod
    def setUpReportAndRecord(cls):
        cls.report_ref = "stock.action_report_delivery"
        cls.record = cls.env.ref("stock.outgoing_shipment_main_warehouse")

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
