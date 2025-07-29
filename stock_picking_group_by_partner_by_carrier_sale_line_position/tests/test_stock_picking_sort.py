# -*- coding: utf-8 -*-
from odoo.tests import common


class TestStockPickingSort(common.TransactionCase):
    def setUp(self):
        super().setUp()
        # Prepare the environment for the tests
        uom = self.env.ref('uom.product_uom_unit')

        # Create a product
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'uom_id': uom.id,
            'uom_po_id': uom.id,
        })

        # Create a partner
        self.partner = self.env['res.partner'].create({
            'name': 'Client Test'
        })

        # Create a delivery method 
        carrier = self.env['delivery.carrier'].create({
            'name': 'Fast Delivery',
            'delivery_type': 'fixed',
            'fixed_price': 10.0,
        })

        # Create a sale order with 3 lines and unordered positions
        SaleOrder = self.env['sale.order']
        SaleLine = self.env['sale.order.line']
        self.order = SaleOrder.create({
            'partner_id': self.partner.id,
            'carrier_id': carrier.id,
        })
        # Lines with intentionally out-of-order positions
        lines_data = [
            {'product_id': self.product.id, 'product_uom_qty': 5, 'product_uom': uom.id, 'position': 30},
            {'product_id': self.product.id, 'product_uom_qty': 2, 'product_uom': uom.id, 'position': 10},
            {'product_id': self.product.id, 'product_uom_qty': 1, 'product_uom': uom.id, 'position': 20},
        ]
        for vals in lines_data:
            SaleLine.create({
                'order_id': self.order.id,
                **vals
            })

        # Create a picking from the sale order
        self.order.action_confirm()
        self.picking = self.order.picking_ids[0]
        # Assign quantities to validate the lines
        moves = self.picking.move_ids_without_package
        for m in moves:
            m.quantity_done = m.product_uom_qty
        self.picking.button_validate()

    def test_get_sorted_moves(self):
        # Method parent defines some order, but here we check our wrapper
        sorted_moves = self.picking._get_sorted_moves()
        positions = [m.sale_line_id.position for m in sorted_moves]
        self.assertEqual(positions, [10, 20, 30],
                         "Els moviments no s'ordenen segons sale_line.position")

    def test_get_sorted_move_lines(self):
        # Generate the move_lines (stock.move.line) and call the method
        lines = self.picking._get_sorted_move_lines()
        positions = [l.move_id.sale_line_id.position for l in lines]
        self.assertEqual(positions, [10, 20, 30],
                         "Les línies de moviment no s'ordenen segons sale_line.position")
