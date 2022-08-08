# Copyright 2017 Tecnativa - David Vidal
# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestStockPickingValued(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestStockPickingValued, cls).setUpClass()
        company = cls.env.user.company_id
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "TAX 15%",
                "amount_type": "percent",
                "type_tax_use": "sale",
                "amount": 15.0,
            }
        )
        cls.tax10 = cls.env["account.tax"].create(
            {
                "name": "TAX 10%",
                "amount_type": "percent",
                "type_tax_use": "sale",
                "amount": 10.0,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test stuff",
                "list_price": 100.0,
                "taxes_id": [(6, 0, cls.tax.ids)],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "price_unit": 100,
                            "product_uom_qty": 1,
                        },
                    )
                ],
                "company_id": company.id,
            }
        )
        cls.sale_order2 = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "price_unit": 100,
                            "product_uom_qty": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "price_unit": 100,
                            "product_uom_qty": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "price_unit": 100,
                            "product_uom_qty": 1,
                            "tax_id": [(6, 0, cls.tax10.ids)],
                        },
                    ),
                ],
                "company_id": company.id,
            }
        )
        cls.sale_order.company_id.tax_calculation_rounding_method = "round_per_line"

    def test_01_confirm_order(self):
        self.assertTrue(self.partner.valued_picking)
        self.sale_order.action_confirm()
        self.assertTrue(len(self.sale_order.picking_ids))
        for picking in self.sale_order.picking_ids:
            picking.action_assign()
            self.assertEqual(picking.amount_untaxed, 100.0)
            self.assertEqual(picking.amount_tax, 15.0)
            self.assertEqual(picking.amount_total, 115.0)

    def test_02_confirm_order(self):
        """Valued picking isn't computed if not reserved"""
        self.sale_order.action_confirm()
        for picking in self.sale_order.picking_ids:
            picking.action_assign()
            picking.do_unreserve()
            self.assertEqual(picking.amount_untaxed, 0.0)
            self.assertEqual(picking.amount_tax, 0.0)
            self.assertEqual(picking.amount_total, 0.0)

    def test_03_tax_rounding_method(self):
        self.sale_order.company_id.tax_calculation_rounding_method = "round_globally"
        self.sale_order.action_confirm()
        self.assertTrue(len(self.sale_order.picking_ids))
        for picking in self.sale_order.picking_ids:
            picking.action_assign()
            self.assertEqual(picking.amount_untaxed, 100.0)
            self.assertEqual(picking.amount_tax, 15.0)
            self.assertEqual(picking.amount_total, 115.0)

    def test_04_lines_distinct_tax(self):
        self.sale_order2.company_id.tax_calculation_rounding_method = "round_globally"
        self.sale_order2.action_confirm()
        self.assertTrue(len(self.sale_order2.picking_ids))
        for picking in self.sale_order2.picking_ids:
            picking.action_assign()
            self.assertEqual(picking.amount_untaxed, 300.0)
            self.assertEqual(picking.amount_tax, 40.0)
            self.assertEqual(picking.amount_total, 340.0)

    def test_05_distinct_qty(self):
        self.assertTrue(self.partner.valued_picking)
        self.sale_order.action_confirm()
        self.assertTrue(len(self.sale_order.picking_ids))
        for picking in self.sale_order.picking_ids:
            picking.action_assign()
            picking.move_line_ids.qty_done = 2.0
            self.assertEqual(picking.amount_untaxed, 200.0)
            self.assertEqual(picking.amount_tax, 30.0)
            self.assertEqual(picking.amount_total, 230.0)
