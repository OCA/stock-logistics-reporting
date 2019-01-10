# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestStockQuantityHistoryLocation(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestStockQuantityHistoryLocation, cls).setUpClass()
        cls.stock_loc = cls.env.ref('stock.stock_location_stock')

    def test_wizard(self):
        self.wizard = self.env['stock.quantity.history'].create({
            "location_id": self.stock_loc.id,
            "include_child_locations": True,
            "compute_at_date": 0,
            "company_owned": True
        })
        wizard = self.wizard.open_table()
        self.assertEquals(wizard['context']['location'], self.stock_loc.id)
