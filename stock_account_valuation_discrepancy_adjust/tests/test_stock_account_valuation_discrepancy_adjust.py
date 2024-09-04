# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import time

from odoo import fields
from odoo.tests.common import TransactionCase


class TestStockAccountValuationDiscrepancy(TransactionCase):
    def setUp(self):
        super(TestStockAccountValuationDiscrepancy, self).setUp()
        # Get required Model
        self.product_model = self.env["product.product"]
        self.template_model = self.env["product.template"]
        self.product_ctg_model = self.env["product.category"]
        self.account_model = self.env["account.account"]
        self.stock_quant_model = self.env["stock.quant"]
        self.stock_location_model = self.env["stock.location"]
        self.account_move_model = self.env["account.move"]
        self.account_move_line_model = self.env["account.move.line"]
        # Get required Model data
        self.company = self.env.ref("base.main_company")

        location = self.stock_location_model.search([("name", "=", "WH")])
        self.location = self.stock_location_model.search(
            [("location_id", "=", location.id)]
        )

        # Account types
        self.stock_journal = self.env["account.journal"].create(
            {"name": "Stock journal", "type": "general", "code": "STK00"}
        )

        expense_type = "expense"
        equity_type = "equity"
        asset_type = "asset_current"

        # Create account for Goods Received Not Invoiced
        name = "Goods Received Not Invoiced"
        code = "grni"
        self.account_grni = self._create_account(equity_type, name, code, self.company)
        # Create account for Cost of Goods Sold
        name = "Cost of Goods Sold"
        code = "cogs"
        self.account_cogs = self._create_account(expense_type, name, code, self.company)

        # Create account for Inventory
        name = "Inventory"
        code = "inventory"
        acc_type = asset_type
        self.account_inventory = self._create_account(
            acc_type, name, code, self.company
        )
        name = "Goods Delivered Not Invoiced"
        code = "gdni"
        self.account_gdni = self._create_account(asset_type, name, code, self.company)
        # Create product category
        self.product_ctg = self._create_product_category()
        # Create a Product with fifo cost
        standard_price = 10.0
        list_price = 20.0
        self.product_fifo_1 = self._create_product(standard_price, False, list_price)
        # Add default quantity
        quantity = 10.00
        self._update_product_qty(self.product_fifo_1, self.location, quantity)

        # Default journal
        journals = self.env["account.journal"].search([("type", "=", "general")])
        self.journal = journals[0]

        # Create a journal entry
        self.move = self._create_account_move(50)
        self.move.action_post()

    def _create_account(self, acc_type, name, code, company):
        """Create an account."""
        account = self.account_model.create(
            {
                "name": name,
                "code": code,
                "account_type": acc_type,
                "company_id": company.id,
            }
        )
        return account

    def _create_product_category(self):
        product_ctg = self.product_ctg_model.create(
            {
                "name": "test_product_ctg",
                "property_stock_valuation_account_id": self.account_inventory.id,
                "property_stock_account_input_categ_id": self.account_grni.id,
                "property_account_expense_categ_id": self.account_cogs.id,
                "property_stock_account_output_categ_id": self.account_gdni.id,
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
                "property_stock_journal": self.stock_journal.id,
            }
        )
        return product_ctg

    def _create_product(self, standard_price, template, list_price):
        """Create a Product variant."""
        if not template:
            template = self.template_model.create(
                {
                    "name": "test_product",
                    "categ_id": self.product_ctg.id,
                    "type": "product",
                    "standard_price": standard_price,
                    "valuation": "real_time",
                }
            )
            return template.product_variant_ids[0]
        product = self.product_model.create(
            {"product_tmpl_id": template.id, "list_price": list_price}
        )
        return product

    def _update_product_qty(self, product, location, quantity):
        """Update Product quantity."""
        quant = self.stock_quant_model.create(
            {
                "location_id": location.id,
                "product_id": product.id,
                "inventory_quantity": quantity,
            }
        )
        quant._apply_inventory()

    def _create_account_move(self, amount):
        date_move = fields.Date.today()

        debit_data = [
            (
                0,
                0,
                {
                    "name": self.product_fifo_1.name,
                    "date": date_move,
                    "product_id": self.product_fifo_1.id,
                    "account_id": self.account_inventory.id,
                    "debit": amount,
                },
            )
        ]
        credit_data = [
            (
                0,
                0,
                {
                    "name": self.product_fifo_1.name,
                    "date": date_move,
                    "product_id": self.product_fifo_1.id,
                    "account_id": self.account_cogs.id,
                    "credit": amount,
                },
            )
        ]
        line_data = debit_data + credit_data
        move = self.account_move_model.create(
            {
                "date": time.strftime("%Y-%m-%d"),
                "ref": "Sample",
                "journal_id": self.journal.id,
                "line_ids": line_data,
            }
        )
        return move

    def test_01_manual_adjustment(self):
        """Test the accounting value after applying the adjustment"""
        self.product_fifo_1._compute_inventory_value()
        self.assertEqual(self.product_fifo_1.stock_value, 100.0)
        self.assertEqual(self.product_fifo_1.account_value, 150.0)
        self.assertEqual(self.product_fifo_1.valuation_discrepancy, -50.0)

        wiz = (
            self.env["wizard.stock.discrepancy.adjustment"]
            .with_context(
                active_model="product.product",
                active_ids=[self.product_fifo_1.id],
                active_id=self.product_fifo_1.id,
            )
            .create(
                {
                    "increase_account_id": self.account_cogs.id,
                    "decrease_account_id": self.account_cogs.id,
                    "journal_id": self.journal.id,
                }
            )
        )
        wiz.with_context(no_delay=True).action_create_adjustment()
        self.product_fifo_1._compute_inventory_value()
        self.assertEqual(self.product_fifo_1.valuation_discrepancy, 0.0)
