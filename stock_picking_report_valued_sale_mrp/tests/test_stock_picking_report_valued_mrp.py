# Copyright 2020 Tecnativa - David Vidal
from odoo.tests import Form, common


class TestStockPickingValuedMrp(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.company
        country = (
            company.account_fiscal_country_id
            or company.country_id
            or cls.env.ref("base.us")
        )
        company.country_id = country
        tax_group = cls.env["account.tax.group"].create(
            {"name": "Test Taxes", "company_id": company.id, "country_id": country.id}
        )
        cls.tax10 = cls.env["account.tax"].create(
            {
                "name": "TAX 10%",
                "amount_type": "percent",
                "type_tax_use": "sale",
                "amount": 10.0,
                "country_id": country.id,
                "tax_group_id": tax_group.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.res_partner = cls.env["res.partner"]
        cls.product_product = cls.env["product.product"]
        cls.product_kit = cls.product_product.create(
            {"name": "Product test 1", "type": "consu"}
        )
        cls.product_kit_comp_1 = cls.product_product.create(
            {"name": "Product Component 1", "type": "consu"}
        )
        cls.product_kit_comp_2 = cls.product_product.create(
            {"name": "Product Component 2", "type": "consu"}
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_id": cls.product_kit.id,
                "product_tmpl_id": cls.product_kit.product_tmpl_id.id,
                "type": "phantom",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {"product_id": cls.product_kit_comp_1.id, "product_qty": 2},
                    ),
                    (
                        0,
                        0,
                        {"product_id": cls.product_kit_comp_2.id, "product_qty": 4},
                    ),
                ],
            }
        )
        cls.product_2 = cls.product_product.create(
            {"name": "Product test 2", "type": "consu"}
        )
        order_form = Form(cls.env["sale.order"])
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = cls.product_kit
            line_form.product_uom_qty = 5
            line_form.price_unit = 29.9
            line_form.tax_ids.clear()
            line_form.tax_ids.add(cls.tax10)
        cls.sale_order_3 = order_form.save()
        cls.sale_order_3.action_confirm()
        # Maybe other modules create additional lines in the create
        # method in sale.order model, so let's find the correct line.
        cls.order_line = cls.sale_order_3.order_line.filtered(
            lambda r: r.product_id == cls.product_kit
        )
        cls.order_out_picking = cls.sale_order_3.picking_ids

    def test_01_picking_confirmed(self):
        for line in self.order_out_picking.move_ids:
            line.quantity = line.product_uom_qty
        self.order_out_picking.button_validate()
        self.assertAlmostEqual(self.order_out_picking.amount_untaxed, 149.5)
        self.assertAlmostEqual(self.order_out_picking.amount_tax, 14.95)
        self.assertAlmostEqual(self.order_out_picking.amount_total, 164.45)
        # Run the report to detect hidden errors
        self.env["ir.actions.report"]._render_qweb_html(
            self.env.ref("stock.action_report_delivery"), self.order_out_picking.ids
        )

    def test_02_two_step_delivery_kit_quantity(self):
        warehouse = self.env.ref("stock.warehouse0")
        warehouse.delivery_steps = "pick_ship"
        self.env.company.tax_calculation_rounding_method = "round_globally"

        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_kit
            line_form.product_uom_qty = 5
            line_form.price_unit = 29.9
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self.tax10)
        sale_order = order_form.save()
        sale_order.action_confirm()

        pick_picking = sale_order.picking_ids.filtered(
            lambda picking: picking.picking_type_id == warehouse.pick_type_id
        )
        self.assertEqual(len(pick_picking), 1)

        for move in pick_picking.move_ids:
            move.quantity = move.product_uom_qty
        pick_picking.button_validate()
        out_picking = sale_order.picking_ids.filtered(
            lambda picking: picking.picking_type_id == warehouse.out_type_id
        )
        self.assertEqual(len(out_picking), 1)
        for move in out_picking.move_ids:
            move.quantity = move.product_uom_qty
        out_picking.button_validate()

        kit_line = out_picking.move_line_ids.filtered("phantom_line")
        self.assertEqual(len(kit_line), 1)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, 5)
        self.assertAlmostEqual(out_picking.amount_untaxed, 149.5)
        self.assertAlmostEqual(out_picking.amount_tax, 14.95)
        self.assertAlmostEqual(out_picking.amount_total, 164.45)

    def test_03_components_per_kit(self):
        component_move = self.order_out_picking.move_ids.filtered(
            lambda move: move.product_id == self.product_kit_comp_1
        )
        self.assertAlmostEqual(component_move._get_components_per_kit(), 2)

        stock_location = self.env.ref("stock.stock_location_stock")
        customer_location = self.env.ref("stock.stock_location_customers")
        move_no_sale_line = self.env["stock.move"].create(
            {
                "product_id": self.product_2.id,
                "product_uom": self.product_2.uom_id.id,
                "product_uom_qty": 1,
                "location_id": stock_location.id,
                "location_dest_id": customer_location.id,
            }
        )
        self.assertEqual(move_no_sale_line._get_components_per_kit(), 0)

        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_2
            line_form.product_uom_qty = 1
        sale_order = order_form.save()
        sale_order.action_confirm()
        self.assertEqual(sale_order.picking_ids.move_ids._get_components_per_kit(), 0)

        move_not_in_bom = self.env["stock.move"].create(
            {
                "product_id": self.product_2.id,
                "product_uom": self.product_2.uom_id.id,
                "product_uom_qty": 1,
                "sale_line_id": self.order_line.id,
                "location_id": stock_location.id,
                "location_dest_id": customer_location.id,
            }
        )
        self.assertEqual(move_not_in_bom._get_components_per_kit(), 0)
