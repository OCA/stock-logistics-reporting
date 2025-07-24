from odoo.tests.common import TransactionCase

class TestStockPickingOrder(TransactionCase):

    def setUp(self):
        super().setUp()
        Product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
        })
        SO = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_12').id,
        })

        SO.write({
            'order_line': [
                (0, 0, {'product_id': Product.id, 'product_uom_qty': 2, 'position': 2}),
                (0, 0, {'product_id': Product.id, 'product_uom_qty': 1, 'position': 1}),
            ],
        })
        SO.action_confirm()
        self.picking = SO.picking_ids[0]

    def test_sorted_moves(self):
        moves = self.picking._get_sorted_moves()
        self.assertEqual(moves[0].sale_line_id.position, 1)

    def test_delivery_report_lines(self):
        report_lines = self.picking.get_delivery_report_lines()

        for line in report_lines:
            if line.get('sale_order_line'):
                self.assertIn('position_formatted', line)
                
