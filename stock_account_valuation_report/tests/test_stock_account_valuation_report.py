# 2020 Copyright ForgeFlow, S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import fields

from odoo.addons.base.tests.common import BaseCommon


class TestStockAccountValuationReport(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Get required Model
        cls.product_model = cls.env["product.product"]
        cls.template_model = cls.env["product.template"]
        cls.product_ctg_model = cls.env["product.category"]
        cls.account_model = cls.env["account.account"]
        cls.quant_model = cls.env["stock.quant"]
        cls.layer_model = cls.env["stock.valuation.layer"]
        cls.stock_location_model = cls.env["stock.location"]
        cls.res_users_model = cls.env["res.users"]
        cls.account_move_model = cls.env["account.move"]
        cls.aml_model = cls.env["account.move.line"]
        cls.journal_model = cls.env["account.journal"]
        # Get required Model data
        cls.product_uom = cls.env.ref("uom.product_uom_unit")
        cls.company = cls.env.ref("base.main_company")
        cls.stock_picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.stock_picking_type_in = cls.env.ref("stock.picking_type_in")
        cls.stock_location_id = cls.env.ref("stock.stock_location_stock").id
        cls.stock_location_customer_id = cls.env.ref(
            "stock.stock_location_customers"
        ).id
        cls.stock_location_supplier_id = cls.env.ref(
            "stock.stock_location_suppliers"
        ).id
        # Account types
        expense_type = "expense"
        equity_type = "equity"
        asset_type = "asset_current"
        # Create account for Goods Received Not Invoiced
        name = "Goods Received Not Invoiced"
        code = "grni"
        account_type = equity_type
        cls.account_grni = cls._create_account(account_type, name, code, cls.company)
        # Create account for Cost of Goods Sold
        name = "Cost of Goods Sold"
        code = "cogs"
        account_type = expense_type
        cls.account_cogs = cls._create_account(account_type, name, code, cls.company)
        # Create account for Goods Delivered Not Invoiced
        name = "Goods Delivered Not Invoiced"
        code = "gdni"
        account_type = expense_type
        cls.account_gdni = cls._create_account(account_type, name, code, cls.company)
        # Create account for Inventory
        name = "Inventory"
        code = "inventory"
        account_type = asset_type
        cls.account_inventory = cls._create_account(
            account_type, name, code, cls.company
        )

        cls.stock_journal = cls.env["account.journal"].create(
            {"name": "Stock journal", "type": "general", "code": "STK00"}
        )
        # Create product category
        cls.product_ctg = cls._create_product_category()

        # Create partners
        cls.supplier = cls.env["res.partner"].create({"name": "Test supplier"})
        cls.customer = cls.env["res.partner"].create({"name": "Test customer"})

        # Create a Product with real cost
        standard_price = 10.0
        list_price = 20.0
        cls.product = cls._create_product(standard_price, False, list_price)

        # Create a vendor
        cls.vendor_partner = cls.env["res.partner"].create({"name": "dropship vendor"})

    @classmethod
    def _create_account(cls, account_type, name, code, company):
        """Create an account."""
        account = cls.account_model.create(
            {
                "name": name,
                "code": code,
                "account_type": account_type,
                "company_ids": [fields.Command.link(company.id)],
            }
        )
        return account

    @classmethod
    def _create_product_category(cls):
        product_ctg = cls.product_ctg_model.create(
            {
                "name": "test_product_ctg",
                "property_stock_valuation_account_id": cls.account_inventory.id,
                "property_stock_account_input_categ_id": cls.account_grni.id,
                "property_account_expense_categ_id": cls.account_cogs.id,
                "property_stock_account_output_categ_id": cls.account_gdni.id,
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
                "property_stock_journal": cls.stock_journal.id,
            }
        )
        return product_ctg

    @classmethod
    def _create_product(cls, standard_price, template, list_price):
        """Create a Product variant."""
        if not template:
            template = cls.template_model.create(
                {
                    "name": "test_product",
                    "categ_id": cls.product_ctg.id,
                    "is_storable": True,
                    "type": "consu",
                    "standard_price": standard_price,
                    "valuation": "real_time",
                }
            )
            return template.product_variant_ids[0]
        product = cls.product_model.create(
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
                "move_ids": [
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
                "move_ids": [
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
        move_dest_id = [fields.Command.link(move_dest_id)] if move_dest_id else False
        return self.env["stock.picking"].create(
            {
                "name": self.stock_picking_type_in.sequence_id._next(),
                "partner_id": self.vendor_partner.id,
                "picking_type_id": self.stock_picking_type_in.id,
                "location_id": self.stock_location_supplier_id,
                "location_dest_id": self.stock_location_id,
                "move_ids": [
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
        picking.move_ids.write({"date": date})
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.quantity = qty
        picking.button_validate()
        # hacking the create_date of the layer in order to test
        self.env.cr.execute(
            """UPDATE stock_valuation_layer SET create_date = %s WHERE id in %s""",
            (date, tuple(picking.move_ids.stock_valuation_layer_ids.ids)),
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
        inv_aml = aml.filtered(lambda li: li.account_id == self.account_inventory)
        balance_inv = sum(inv_aml.mapped("balance"))
        self.assertEqual(balance_inv, 10.0)
        move = in_picking.move_ids
        layer = self.layer_model.search([("stock_move_id", "=", move.id)])
        self.assertEqual(layer.remaining_value, 10.0)
        # The accounting value and the stock value match
        self.assertEqual(self.product.stock_value, 10.0)
        self.assertEqual(self.product.account_value, 10.0)
        # The qty also match
        self.assertEqual(self.product.qty_at_date, 1.0)
        self.assertEqual(self.product.account_qty_at_date, 1.0)
        # Layer can be opened from the product
        action = self.product.action_view_valuation_layers()
        self.assertEqual(
            self.env[action["res_model"]].search(action["domain"]),
            layer,
        )
        # Create an out picking
        out_picking = self._create_delivery(self.product, 1)
        self._do_picking(out_picking, fields.Datetime.now(), 1.0)
        # The original layer must have been reduced.
        self.assertEqual(layer.remaining_qty, 0.0)
        self.assertEqual(layer.remaining_value, 0.0)
        # The layer out took that out
        move = out_picking.move_ids
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
        inv_aml = aml.filtered(lambda li: li.account_id == self.account_inventory)
        balance_inv = sum(inv_aml.mapped("balance"))
        self.assertEqual(balance_inv, 0.0)
        # There are two a stock valuation layers associated to this product
        move = dropship_picking.move_ids
        layers = self.layer_model.search([("stock_move_id", "=", move.id)])
        self.assertEqual(len(layers), 2)
        in_layer = layers.filtered(lambda li: li.quantity > 0)
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
        inv_aml = aml.filtered(lambda li: li.account_id == self.account_inventory)
        balance_inv = sum(inv_aml.mapped("balance"))
        self.assertEqual(balance_inv, 10.0)
        move = in_picking.move_ids
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
        inv_aml = aml.filtered(lambda li: li.account_id == self.account_inventory)
        balance_inv = sum(inv_aml.mapped("balance"))
        self.assertEqual(balance_inv, 50.0)
        move2 = in_picking2.move_ids
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
