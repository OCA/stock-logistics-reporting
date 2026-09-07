# 2020 Copyright ForgeFlow, S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.fields import Domain

from odoo.addons.stock_account.tests.common import TestStockValuationCommon


class TestStockAccountValuationReport(TestStockValuationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.aml_model = cls.env["account.move.line"]

    def test_01_stock_receipt(self):
        """Receive into stock and ship to the customer"""
        self._use_inventory_location_accounting()
        move = self._make_in_move(self.product_fifo_auto, quantity=1, unit_cost=10.0)
        inv_aml = self.aml_model.search(
            Domain("product_id", "=", self.product_fifo_auto.id)
        )
        balance_inv = sum(inv_aml.mapped("balance"))
        self.assertEqual(balance_inv, 0.0)
        self.assertEqual(move.remaining_value, 10.0)
        # The accounting value and the stock value do not match
        self.assertEqual(self.product_fifo_auto.stock_value, 10.0)
        self.assertEqual(self.product_fifo_auto.account_value, 0.0)
        self.assertEqual(self.product_fifo_auto.qty_at_date, 1.0)
        # Stock Move can be opened from the product
        action = self.product_fifo_auto.action_view_valuation_moves()
        self.assertEqual(
            self.env[action["res_model"]].search(action["domain"]),
            move,
        )
        # Create an out move
        move_out = self._make_out_move(self.product_fifo_auto, 1.0)
        self.assertEqual(move.remaining_qty, 0.0)
        self.assertEqual(move.remaining_value, 0.0)
        self.assertEqual(move_out.value, 10.0)
        # The report shows the material is gone
        self.product_fifo_auto._compute_inventory_value()
        self.assertEqual(self.product_fifo_auto.stock_value, 0.0)
        self.assertEqual(self.product_fifo_auto.account_value, 0.0)
        self.assertEqual(self.product_fifo_auto.qty_at_date, 0.0)

    def test_02_stock_receipt_several_costs_several_dates(self):
        """Receive into stock at different cost"""
        self._use_inventory_location_accounting()
        move = self._make_in_move(self.product_fifo_auto, quantity=1.0, unit_cost=10.0)
        # This will not create any journal entry
        inv_aml = self.aml_model.search(
            Domain("product_id", "=", self.product_fifo_auto.id)
        )
        balance_inv = sum(inv_aml.mapped("balance"))
        self.assertEqual(balance_inv, 0.0)
        self.assertEqual(move.remaining_value, 10.0)
        # Receive more
        move2 = self._make_in_move(self.product_fifo_auto, quantity=2.0, unit_cost=20.0)
        # This will not create any journal entry
        inv_aml = self.aml_model.search(
            Domain("product_id", "=", self.product_fifo_auto.id)
        )
        balance_inv = sum(inv_aml.mapped("balance"))
        self.assertEqual(balance_inv, 0.0)
        self.assertEqual(move2.remaining_value, 40.0)
        # Now we check the report reflects the same
        self.assertEqual(self.product_fifo_auto.stock_value, 50.0)
        self.assertEqual(self.product_fifo_auto.account_value, 0.0)
        self.assertEqual(self.product_fifo_auto.qty_at_date, 3.0)

    def test_03_stock_receipt_with_invoice(self):
        """Receive into stock, create bill, ship to customer with invoice"""
        self._use_inventory_location_accounting()
        self._make_in_move(self.product_fifo_auto, 1, unit_cost=10.0)
        self.product_fifo_auto._compute_inventory_value()
        self.assertEqual(self.product_fifo_auto.stock_value, 10.0)
        self.assertEqual(self.product_fifo_auto.account_value, 0.0)
        self.assertEqual(self.product_fifo_auto.qty_at_date, 1.0)
        self.assertEqual(self.product_fifo_auto.valuation_discrepancy, 10.0)
        self._create_bill(self.product_fifo_auto, 1.0, price_unit=10.0)
        self.product_fifo_auto._compute_inventory_value()
        self.assertEqual(self.product_fifo_auto.stock_value, 10.0)
        self.assertEqual(self.product_fifo_auto.account_value, 10.0)
        self.assertEqual(self.product_fifo_auto.qty_at_date, 1.0)
        self.assertEqual(self.product_fifo_auto.valuation_discrepancy, 0.0)
        # check accounting entries
        inv_aml = self.aml_model.search(
            Domain("product_id", "=", self.product_fifo_auto.id)
        )
        self.assertEqual(sum(inv_aml.mapped("balance")), 10.0)
        self.assertEqual(sum(inv_aml.mapped("quantity")), 1.0)
        self._make_out_move(self.product_fifo_auto, 1.0)
        # Before customer invoice: stock is empty but accounting still shows value
        self.product_fifo_auto._compute_inventory_value()
        self.assertEqual(self.product_fifo_auto.stock_value, 0.0)
        self.assertEqual(self.product_fifo_auto.account_value, 10.0)
        self.assertEqual(self.product_fifo_auto.qty_at_date, 0.0)
        self.assertEqual(self.product_fifo_auto.valuation_discrepancy, -10.0)

        self._create_invoice(self.product_fifo_auto, 1.0, price_unit=10.0)
        # After customer invoice: everything should be zero
        self.product_fifo_auto._compute_inventory_value()
        self.assertEqual(self.product_fifo_auto.stock_value, 0.0)
        self.assertEqual(self.product_fifo_auto.account_value, 0.0)
        self.assertEqual(self.product_fifo_auto.qty_at_date, 0.0)
        self.assertEqual(self.product_fifo_auto.valuation_discrepancy, 0.0)

        # Verify final accounting balance is zero
        inv_aml = self.aml_model.search(
            Domain("product_id", "=", self.product_fifo_auto.id)
        )
        self.assertEqual(sum(inv_aml.mapped("balance")), 0.0)

    def test_04_qty_discrepancy(self):
        """Without a valuation entry, the accounting quantity does not move"""
        self._use_inventory_location_accounting()
        self._make_in_move(self.product_fifo_auto, quantity=1, unit_cost=10.0)
        self.product_fifo_auto._compute_inventory_value()
        # No journal entry was created for this move (no location valuation
        # account configured for supplier/customer), so the accounting
        # quantity does not move even though the physical stock did.
        self.assertEqual(self.product_fifo_auto.qty_at_date, 1.0)
        self.assertEqual(self.product_fifo_auto.account_qty_at_date, 0.0)
        self.assertEqual(self.product_fifo_auto.qty_discrepancy, 1.0)
        discrepancy_ids = self.env["product.product"]._get_qty_discrepancy_product_ids()
        self.assertIn(self.product_fifo_auto.id, discrepancy_ids)

        self._make_out_move(self.product_fifo_auto, 1.0)
        self.product_fifo_auto._compute_inventory_value()
        self.assertEqual(self.product_fifo_auto.qty_at_date, 0.0)
        self.assertEqual(self.product_fifo_auto.account_qty_at_date, 0.0)
        self.assertEqual(self.product_fifo_auto.qty_discrepancy, 0.0)

    def test_05_qty_discrepancy_with_bill_and_invoice(self):
        """A vendor bill counts as a positive accounting quantity and a
        customer invoice as a negative one, on top of the same valuation
        account, mirroring test_03 but for quantity instead of value"""
        self._use_inventory_location_accounting()
        self._make_in_move(self.product_fifo_auto, 1, unit_cost=10.0)
        self.product_fifo_auto._compute_inventory_value()
        self.assertEqual(self.product_fifo_auto.qty_at_date, 1.0)
        self.assertEqual(self.product_fifo_auto.account_qty_at_date, 0.0)
        self.assertEqual(self.product_fifo_auto.qty_discrepancy, 1.0)

        self._create_bill(self.product_fifo_auto, 1.0, price_unit=10.0)
        self.product_fifo_auto._compute_inventory_value()
        # The bill line posted to the valuation account counts as +1
        self.assertEqual(self.product_fifo_auto.qty_at_date, 1.0)
        self.assertEqual(self.product_fifo_auto.account_qty_at_date, 1.0)
        self.assertEqual(self.product_fifo_auto.qty_discrepancy, 0.0)

        self._make_out_move(self.product_fifo_auto, 1.0)
        self.product_fifo_auto._compute_inventory_value()
        # Delivery alone posts no journal entry, so accounting quantity
        # still only reflects the bill
        self.assertEqual(self.product_fifo_auto.qty_at_date, 0.0)
        self.assertEqual(self.product_fifo_auto.account_qty_at_date, 1.0)
        self.assertEqual(self.product_fifo_auto.qty_discrepancy, -1.0)

        self._create_invoice(self.product_fifo_auto, 1.0, price_unit=10.0)
        self.product_fifo_auto._compute_inventory_value()
        # The customer invoice's COGS line credits the valuation account,
        # counting as -1, netting the bill's +1 back to 0
        self.assertEqual(self.product_fifo_auto.qty_at_date, 0.0)
        self.assertEqual(self.product_fifo_auto.account_qty_at_date, 0.0)
        self.assertEqual(self.product_fifo_auto.qty_discrepancy, 0.0)
