# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.stock_account.tests.common import TestStockValuationCommon


class TestAccountMoveLineStockQuantity(TestStockValuationCommon):
    def setUp(self):
        super().setUp()
        # A move only posts a valuation entry when one of its locations
        # carries a valuation account. The vendor and customer locations are
        # virtual, so theirs is the counterpart for value entering or leaving
        # the company.
        counterpart_in = self.env["account.account"].create(
            {
                "name": "Stock Counterpart (Vendors)",
                "code": "100150",
                "account_type": "asset_current",
            }
        )
        counterpart_out = self.env["account.account"].create(
            {
                "name": "Stock Counterpart (Customers)",
                "code": "100151",
                "account_type": "asset_current",
            }
        )
        self.supplier_location.valuation_account_id = counterpart_in.id
        self.customer_location.valuation_account_id = counterpart_out.id

    def test_in_move_sets_positive_stock_quantity(self):
        move = self._make_in_move(self.product_fifo_auto, quantity=5, unit_cost=10.0)
        aml = self.env["account.move.line"].search(
            [("move_id", "in", move.account_move_id.ids)]
        )
        valuation_aml = aml.filtered(
            lambda line: line.account_id == self.account_stock_valuation
        )
        counterpart_aml = aml - valuation_aml
        self.assertEqual(sum(valuation_aml.mapped("stock_quantity")), 5.0)
        self.assertEqual(sum(counterpart_aml.mapped("stock_quantity")), 0.0)

    def test_out_move_sets_negative_stock_quantity(self):
        self._make_in_move(self.product_fifo_auto, quantity=5, unit_cost=10.0)
        move_out = self._make_out_move(self.product_fifo_auto, quantity=2)
        aml = self.env["account.move.line"].search(
            [("move_id", "in", move_out.account_move_id.ids)]
        )
        valuation_aml = aml.filtered(
            lambda line: line.account_id == self.account_stock_valuation
        )
        self.assertEqual(sum(valuation_aml.mapped("stock_quantity")), -2.0)

    def test_manual_entry_defaults_to_zero(self):
        invoice = self._create_bill(self.product_fifo_auto, 1.0, price_unit=10.0)
        self.assertEqual(sum(invoice.line_ids.mapped("stock_quantity")), 0.0)
