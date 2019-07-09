# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestStockQuantityHistoryLocation(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestStockQuantityHistoryLocation, cls).setUpClass()
        cls.supplier_location = cls.env.ref('stock.stock_location_suppliers')
        cls.main_company = cls.env.ref('base.main_company')
        cls.product = cls.env.ref('product.product_product_3')
        cls.test_stock_loc = cls.env['stock.location'].create({
            'usage': 'internal',
            'name': 'Test Stock Location',
            'company_id': cls.main_company.id
        })
        cls.child_test_stock_loc = cls.env['stock.location'].create({
            'usage': 'internal',
            'name': 'Child Test Stock Location',
            'location_id': cls.test_stock_loc.id,
            'company_id': cls.main_company.id
        })
        # Create a move for the past
        move = cls.env['stock.move'].create({
            'name': 'Stock move in',
            'location_id': cls.supplier_location.id,
            'location_dest_id': cls.child_test_stock_loc.id,
            'product_id': cls.product.id,
            'product_uom': cls.product.uom_id.id,
            'product_uom_qty': 100.0,
        })
        move._action_confirm()
        move._action_assign()
        move_line = move.move_line_ids[0]
        move_line.qty_done = 100.0
        move._action_done()
        move.date = "2019-08-11"

    def test_wizard_past_date(self):
        wizard = self.env['stock.quantity.history'].create({
            "location_id": self.test_stock_loc.id,
            "include_child_locations": True,
            "compute_at_date": 1,
            "date": "2019-08-12",
        })
        action = wizard.with_context(company_owned=True).open_table()
        self.assertEquals(
            self.product.with_context(action['context']).qty_available, 100.0)
        self.assertEquals(self.product.with_context(
            location=self.child_test_stock_loc.id,
            to_date="2019-08-10").qty_available, 0.0)

    def test_wizard_current(self):
        wizard = self.env['stock.quantity.history'].create({
            "location_id": self.test_stock_loc.id,
            "include_child_locations": True,
            "compute_at_date": 0,
        })
        action = wizard.with_context().open_table()
        self.assertEquals(action['context']['location'],
                          self.test_stock_loc.id)
