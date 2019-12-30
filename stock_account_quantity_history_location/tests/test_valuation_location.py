# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.stock_quantity_history_location.tests import (
    test_stock_quantity_history_location
)


class TestValuationLocation(test_stock_quantity_history_location
                            .TestStockQuantityHistoryLocation):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['product.price.history'].create({
            'datetime': '2019-08-12',
            'product_id': cls.product.id,
            'cost': 35.01,
        })
        cls.env['product.price.history'].create({
            'datetime': '2020-01-01',
            'product_id': cls.product.id,
            'cost': 33.33,
        })
        cls.product.categ_id.property_cost_method = 'standard'
        cls.test_stock_loc2 = cls.env['stock.location'].create({
            'usage': 'internal',
            'name': 'Test Stock Location 2',
            'company_id': cls.main_company.id
        })
        # Create a move for the past
        move = cls.env['stock.move'].create({
            'name': 'Stock move in',
            'location_id': cls.supplier_location.id,
            'location_dest_id': cls.test_stock_loc2.id,
            'product_id': cls.product.id,
            'product_uom': cls.product.uom_id.id,
            'product_uom_qty': 50.0,
        })
        move._action_confirm()
        move._action_assign()
        move_line = move.move_line_ids[0]
        move_line.qty_done = 50.0
        move._action_done()
        move.date = "2020-01-01"

    def test_stock_location_valuation(self):
        wizard = self.env['stock.quantity.history'].create({
            "location_id": self.test_stock_loc2.id,
            "include_child_locations": True,
            "compute_at_date": 1,
            "date": "2020-01-01",
        })
        action = wizard.with_context(
            company_owned=True, valuation=True).open_table()
        self.assertAlmostEqual(
            self.product.with_context(action['context']).stock_value, 1666.5)
