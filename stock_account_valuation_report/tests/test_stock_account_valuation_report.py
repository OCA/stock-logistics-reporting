# 2020 Copyright ForgeFlow, S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestStockAccountValuationReport(TransactionCase):
    def setUp(self):
        super(TestStockAccountValuationReport, self).setUp()
        # Get required Model
        self.product_model = self.env["product.product"]
        self.template_model = self.env["product.template"]
        self.product_ctg_model = self.env["product.category"]
        self.account_model = self.env["account.account"]
        self.quant_model = self.env["stock.quant"]
        self.layer_model = self.env["stock.valuation.layer"]
        self.stock_location_model = self.env["stock.location"]
        self.res_users_model = self.env["res.users"]
        self.account_move_model = self.env["account.move"]
        self.aml_model = self.env["account.move.line"]
        self.journal_model = self.env["account.journal"]
        # Get required Model data
        self.product_uom = self.env.ref("uom.product_uom_unit")
        self.company = self.env.ref("base.main_company")
        self.stock_picking_type_out = self.env.ref("stock.picking_type_out")
        self.stock_picking_type_in = self.env.ref("stock.picking_type_in")
        self.stock_location_id = self.ref("stock.stock_location_stock")
        self.stock_location_customer_id = self.ref("stock.stock_location_customers")
        self.stock_location_supplier_id = self.ref("stock.stock_location_suppliers")
        # Account types
        expense_type = self.env.ref("account.data_account_type_expenses")
        equity_type = self.env.ref("account.data_account_type_equity")
        asset_type = self.env.ref("account.data_account_type_fixed_assets")
        # Create account for Goods Received Not Invoiced
        name = "Goods Received Not Invoiced"
        code = "grni"
        acc_type = equity_type
        self.account_grni = self._create_account(acc_type, name, code, self.company)
        # Create account for Cost of Goods Sold
        name = "Cost of Goods Sold"
        code = "cogs"
        acc_type = expense_type
        self.account_cogs = self._create_account(acc_type, name, code, self.company)
        # Create account for Goods Delivered Not Invoiced
        name = "Goods Delivered Not Invoiced"
        code = "gdni"
        acc_type = expense_type
        self.account_gdni = self._create_account(acc_type, name, code, self.company)
        # Create account for Inventory
        name = "Inventory"
        code = "inventory"
        acc_type = asset_type
        self.account_inventory = self._create_account(
            acc_type, name, code, self.company
        )

        self.stock_journal = self.env["account.journal"].create(
            {"name": "Stock journal", "type": "general", "code": "STK00"}
        )
        # Create product category
        self.product_ctg = self._create_product_category()

        # Create partners
        self.supplier = self.env["res.partner"].create({"name": "Test supplier"})
        self.customer = self.env["res.partner"].create({"name": "Test customer"})

        # Create a Product with real cost
        standard_price = 10.0
        list_price = 20.0
        self.product = self._create_product(standard_price, False, list_price)

        # Create a vendor
        self.vendor_partner = self.env["res.partner"].create(
            {"name": "dropship vendor"}
        )

    def _create_user(self, login, groups, company):
        """Create a user."""
        group_ids = [group.id for group in groups]
        user = self.res_users_model.with_context(no_reset_password=True).create(
            {
                "name": "Test User",
                "login": login,
                "password": "demo",
                "email": "test@yourcompany.com",
                "company_id": company.id,
                "company_ids": [(4, company.id)],
                "groups_id": [(6, 0, group_ids)],
            }
        )
        return user

    def _create_account(self, acc_type, name, code, company):
        """Create an account."""
        account = self.account_model.create(
            {
                "name": name,
                "code": code,
                "user_type_id": acc_type.id,
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

    def _create_delivery(self, product, qty, price_unit=10.0):
        return self.env["stock.picking"].create(
            {
                "name": self.stock_picking_type_out.sequence_id._next(),
                "partner_id": self.customer.id,
                "picking_type_id": self.stock_picking_type_out.id,
                "location_id": self.stock_location_id,
                "location_dest_id": self.stock_location_customer_id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": qty,
                            "price_unit": price_unit,
                            "location_id": self.stock_location_id,
                            "location_dest_id": self.stock_location_customer_id,
                            "procure_method": "make_to_stock",
                        },
                    )
                ],
            }
        )

    def _create_drophip_picking(self, product, qty, price_unit=10.0):
        return self.env["stock.picking"].create(
            {
                "name": self.stock_picking_type_out.sequence_id._next(),
                "partner_id": self.customer.id,
                "picking_type_id": self.stock_picking_type_out.id,
                "location_id": self.stock_location_supplier_id,
                "location_dest_id": self.stock_location_customer_id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": qty,
                            "price_unit": price_unit,
                            "location_id": self.stock_location_supplier_id,
                            "location_dest_id": self.stock_location_customer_id,
                        },
                    )
                ],
            }
        )

    def _create_receipt(self, product, qty, move_dest_id=False, price_unit=10.0):
        move_dest_id = [(4, move_dest_id)] if move_dest_id else False
        return self.env["stock.picking"].create(
            {
                "name": self.stock_picking_type_in.sequence_id._next(),
                "partner_id": self.vendor_partner.id,
                "picking_type_id": self.stock_picking_type_in.id,
                "location_id": self.stock_location_supplier_id,
                "location_dest_id": self.stock_location_id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": qty,
                            "price_unit": price_unit,
                            "move_dest_ids": move_dest_id,
                            "location_id": self.stock_location_supplier_id,
                            "location_dest_id": self.stock_location_id,
                            "procure_method": "make_to_stock",
                        },
                    )
                ],
            }
        )

    def _do_picking(self, picking, date, qty):
        """Do picking with only one move on the given date."""
        picking.write({"date": date})
        picking.move_lines.write({"date": date})
        picking.action_confirm()
        picking.action_assign()
        picking.move_lines.quantity_done = qty
        picking.button_validate()
        # hacking the create_date of the layer in order to test
        self.env.cr.execute(
            """UPDATE stock_valuation_layer SET create_date = %s WHERE id in %s""",
            (date, tuple(picking.move_lines.stock_valuation_layer_ids.ids)),
        )
        return True

    def test_01_stock_receipt(self):
        """Receive into stock and ship to the customer"""
        # Create receipt
        in_picking = self._create_receipt(self.product, 1.0)
        # Receive one unit.
        self._do_picking(in_picking, fields.Datetime.now(), 1.0)
        # This will create an entry:
        #              dr  cr
        # GRNI              10
        # Inventory    10

        # Inventory is 10
        aml = self.aml_model.search([("product_id", "=", self.product.id)])
        inv_aml = aml.filtered(lambda l: l.account_id == self.account_inventory)
        balance_inv = sum(inv_aml.mapped("balance"))
        self.assertEqual(balance_inv, 10.0)
        move = in_picking.move_lines
        layer = self.layer_model.search([("stock_move_id", "=", move.id)])
        self.assertEqual(layer.remaining_value, 10.0)
        # The accounting value and the stock value match
        self.assertEqual(self.product.stock_value, 10.0)
        self.assertEqual(self.product.account_value, 10.0)
        # The qty also match
        self.assertEqual(self.product.qty_at_date, 1.0)
        self.assertEqual(self.product.account_qty_at_date, 1.0)
        # Create an out picking
        out_picking = self._create_delivery(self.product, 1)
        self._do_picking(out_picking, fields.Datetime.now(), 1.0)
        # The original layer must have been reduced.
        self.assertEqual(layer.remaining_qty, 0.0)
        self.assertEqual(layer.remaining_value, 0.0)
        # The layer out took that out
        move = out_picking.move_lines
        layer = self.layer_model.search([("stock_move_id", "=", move.id)])
        self.assertEqual(layer.value, -10.0)
        # The report shows the material is gone
        self.product._compute_inventory_value()
        self.assertEqual(self.product.stock_value, 0.0)
        self.assertEqual(self.product.account_value, 0.0)
        self.assertEqual(self.product.qty_at_date, 0.0)
        self.assertEqual(self.product.account_qty_at_date, 0.0)

    def test_02_drop_ship(self):
        """Drop shipment from vendor to customer"""
        # Create drop_shipment
        dropship_picking = self._create_drophip_picking(self.product, 1.0)
        # Receive one unit.
        self._do_picking(dropship_picking, fields.Datetime.now(), 1.0)
        # This will create the following entries
        #              dr  cr
        # GRNI              10
        # Inventory    10
        #              dr  cr
        # Inventory        10
        # GDNI         10
        aml = self.aml_model.search([("product_id", "=", self.product.id)])
        # Inventory is 0
        inv_aml = aml.filtered(lambda l: l.account_id == self.account_inventory)
        balance_inv = sum(inv_aml.mapped("balance"))
        self.assertEqual(balance_inv, 0.0)
        # There are two a stock valuation layers associated to this product
        move = dropship_picking.move_lines
        layers = self.layer_model.search([("stock_move_id", "=", move.id)])
        self.assertEqual(len(layers), 2)
        in_layer = layers.filtered(lambda l: l.quantity > 0)
        # Check that the layer created for the outgoing move
        self.assertEqual(in_layer.remaining_qty, 0.0)
        self.assertEqual(in_layer.remaining_value, 0.0)
        # The report shows the material is gone
        self.assertEqual(self.product.stock_value, 0.0)
        self.assertEqual(self.product.account_value, 0.0)
        self.assertEqual(self.product.qty_at_date, 0.0)
        self.assertEqual(self.product.account_qty_at_date, 0.0)

    def test_03_stock_receipt_several_costs_several_dates(self):
        """Receive into stock at different cost"""
        # Create receipt
        in_picking = self._create_receipt(self.product, 1.0)
        # Receive one unit.
        self._do_picking(in_picking, fields.Datetime.now(), 1.0)
        # This will create an entry:
        #              dr  cr
        # GRNI              10
        # Inventory    10

        # Inventory is 10
        aml = self.aml_model.search([("product_id", "=", self.product.id)])
        inv_aml = aml.filtered(lambda l: l.account_id == self.account_inventory)
        balance_inv = sum(inv_aml.mapped("balance"))
        self.assertEqual(balance_inv, 10.0)
        move = in_picking.move_lines
        layer = self.layer_model.search([("stock_move_id", "=", move.id)])
        self.assertEqual(layer.remaining_value, 10.0)
        # Receive more
        in_picking2 = self._create_receipt(self.product, 2.0, False, 20.0)
        # Receive two unitsat double cost.
        self._do_picking(
            in_picking2, fields.Datetime.now() + relativedelta(days=3), 2.0
        )
        # This will create an entry:
        #              dr  cr
        # GRNI              40
        # Inventory    40

        # Inventory is 50
        aml = self.aml_model.search([("product_id", "=", self.product.id)])
        inv_aml = aml.filtered(lambda l: l.account_id == self.account_inventory)
        balance_inv = sum(inv_aml.mapped("balance"))
        self.assertEqual(balance_inv, 50.0)
        move2 = in_picking2.move_lines
        layer = self.layer_model.search([("stock_move_id", "=", move2.id)])
        self.assertEqual(layer.remaining_value, 40.0)
        # Now we check the report reflects the same
        self.assertEqual(self.product.stock_value, 50.0)
        self.assertEqual(self.product.account_value, 50.0)
        self.assertEqual(self.product.qty_at_date, 3.0)
        self.assertEqual(self.product.account_qty_at_date, 3.0)
        # That is the value tomorrow, today it is less
        # We hack the date in the account move, not a topic for this module
        aml_layer = layer.account_move_id.line_ids
        self.env.cr.execute(
            """UPDATE account_move_line SET date = %s WHERE id in %s""",
            (fields.Datetime.now() + relativedelta(days=3), tuple(aml_layer.ids)),
        )
        self.product.with_context(
            at_date=fields.Datetime.now() + relativedelta(days=1)
        )._compute_inventory_value()
        self.assertEqual(self.product.stock_value, 10.0)
        self.assertEqual(self.product.account_value, 10.0)
        self.assertEqual(self.product.qty_at_date, 1.0)
        self.assertEqual(self.product.account_qty_at_date, 1.0)
