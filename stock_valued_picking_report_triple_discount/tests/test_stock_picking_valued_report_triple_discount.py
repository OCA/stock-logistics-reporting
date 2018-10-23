# -*- coding: utf-8 -*-
# Copyright 2017 Luis M. Ontalba - Tecnativa <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestStockPickingValuedTripleDiscount(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestStockPickingValuedTripleDiscount, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Mr. Odoo',
        })
        cls.product1 = cls.env['product.product'].create({
            'name': 'Test Product 1',
        })
        cls.product2 = cls.env['product.product'].create({
            'name': 'Test Product 2',
        })
        cls.tax = cls.env['account.tax'].create({
            'name': 'TAX 15%',
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'amount': 15.0,
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id
        })
        so_line = cls.env['sale.order.line']
        cls.so_line1 = so_line.create({
            'order_id': cls.order.id,
            'product_id': cls.product1.id,
            'name': 'Line 1',
            'product_uom_qty': 1.0,
            'tax_id': [(6, 0, [cls.tax.id])],
            'price_unit': 600.0,
        })
        cls.so_line2 = so_line.create({
            'order_id': cls.order.id,
            'product_id': cls.product2.id,
            'name': 'Line 2',
            'product_uom_qty': 10.0,
            'tax_id': [(6, 0, [cls.tax.id])],
            'price_unit': 60.0,
        })

    def test_valued_picking_classic_discount(self):
        """ Tests with single discount """
        self.so_line1.discount = 50.0
        self.so_line2.discount = 75.0
        self.assertEqual(self.so_line1.price_subtotal, 300.0)
        self.assertEqual(self.so_line2.price_subtotal, 150.0)
        self.assertEqual(self.order.amount_untaxed, 450.0)
        self.assertEqual(self.order.amount_tax, 67.5)
        self.order.action_confirm()
        self.assertTrue(len(self.order.picking_ids))
        for picking in self.order.picking_ids:
            self.assertEqual(picking.amount_untaxed, 450.0)
            self.assertEqual(picking.amount_tax, 67.5)
            self.assertEqual(picking.amount_total, 517.5)

    def test_valued_picking_classic_discount_mix_taxed(self):
        """ Mix taxed and untaxed """
        self.so_line1.tax_id = False
        self.so_line1.discount = 50.0
        self.so_line2.discount = 75.0
        self.assertEqual(self.order.amount_tax, 22.5)
        self.order.action_confirm()
        self.assertTrue(len(self.order.picking_ids))
        for picking in self.order.picking_ids:
            self.assertEqual(picking.amount_tax, 22.5)

    def test_valued_picking_triple_discount(self):
        """ Tests with triple discount """
        self.so_line1.discount = 50.0
        self.so_line1.discount2 = 50.0
        self.so_line1.discount3 = 50.0
        self.assertEqual(self.so_line1.price_subtotal, 75.0)
        self.assertEqual(self.order.amount_untaxed, 675.0)
        self.assertEqual(self.order.amount_tax, 101.25)
        self.order.action_confirm()
        self.assertTrue(len(self.order.picking_ids))
        for picking in self.order.picking_ids:
            self.assertEqual(picking.amount_untaxed, 675.0)
            self.assertEqual(picking.amount_tax, 101.25)
            self.assertEqual(picking.amount_total, 776.25)
