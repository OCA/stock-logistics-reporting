# Copyright 2019-21 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStockReportQuantityByLocation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestStockReportQuantityByLocation, cls).setUpClass()
        cls.stock_loc = cls.env.ref("stock.stock_location_stock")

    def test_wizard(self):
        self.wizard = self.env["stock.report.quantity.by.location.prepare"].create(
            {"location_ids": [(4, self.stock_loc.id)]}
        )
        wiz_creator = self.wizard.open()
        wizard_lines = self.env["stock.report.quantity.by.location"].search(
            wiz_creator["domain"]
        )
        self.assertFalse(any(wiz.location_id != self.stock_loc for wiz in wizard_lines))
