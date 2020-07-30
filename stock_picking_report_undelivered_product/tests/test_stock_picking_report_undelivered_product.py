# Copyright 2020 Sergio Teruel - Tecnativa <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import common
from odoo.tests.common import Form


class TestStockPickingReportUndeliveredProduct(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.ResPartner = self.env['res.partner']
        self.ProductProduct = self.env['product.product']
        self.StockPicking = self.env['stock.picking']
        self.StockQuant = self.env['stock.quant']

        self.warehouse = self.env.ref('stock.warehouse0')
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_location = self.env.ref('stock.stock_location_customers')
        self.picking_type_out = self.env.ref('stock.picking_type_out')

        self.partner_display = self.ResPartner.create({
            'name': 'Partner for test display',
            'customer': True,
            'display_undelivered_in_picking': True,
        })
        self.partner_no_display = self.ResPartner.create({
            'name': 'Partner for test on display',
            'customer': True,
            'display_undelivered_in_picking': False,
        })

        self.product_display = self.ProductProduct.create({
            'name': 'Test product undelivered display',
            'display_undelivered_in_picking': True,
            'type': 'product',
        })
        self.product_no_display = self.ProductProduct.create({
            'name': 'Test product undelivered no display',
            'display_undelivered_in_picking': False,
            'type': 'product',
        })
        self.product_no_display_wo_stock = self.ProductProduct.create({
            'name': 'Test product undelivered no display without stock',
            'display_undelivered_in_picking': False,
            'type': 'product',
        })
        self.StockQuant.create({
            'product_id': self.product_no_display.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 2000,
        })

    def _create_picking(self, partner):
        picking_form = Form(self.StockPicking)
        picking_form.picking_type_id = self.picking_type_out
        picking_form.partner_id = partner

        with picking_form.move_ids_without_package.new() as line:
            line.product_id = self.product_display
            line.product_uom_qty = 50.00
        with picking_form.move_ids_without_package.new() as line:
            line.product_id = self.product_no_display
            line.product_uom_qty = 20.00
        with picking_form.move_ids_without_package.new() as line:
            line.product_id = self.product_no_display_wo_stock
            line.product_uom_qty = 20.00
        return picking_form.save()

    def test_displayed_customer(self):
        picking = self._create_picking(self.partner_display)
        picking.action_confirm()
        picking.action_assign()
        picking.move_line_ids.qty_done = 10.00
        picking.action_done()
        # Cancel backorder
        picking.backorder_ids.action_cancel()
        res = self.env['ir.actions.report']._get_report_from_name(
            'stock.report_deliveryslip'
        ).render_qweb_html(picking.ids)
        self.assertIn("undelivered_product", str(res[0]))

    def test_no_displayed_customer(self):
        picking = self._create_picking(self.partner_no_display)
        picking.action_confirm()
        picking.action_assign()
        picking.move_line_ids.qty_done = 10.00
        picking.action_done()
        # Cancel backorder
        picking.backorder_ids.action_cancel()
        res = self.env['ir.actions.report']._get_report_from_name(
            'stock.report_deliveryslip'
        ).render_qweb_html(picking.ids)
        self.assertNotIn("undelivered_product", str(res[0]))

    def test_no_displayed_product(self):
        picking = self._create_picking(self.partner_display)
        picking.move_lines.filtered(
            lambda l: l.product_id == self.product_display).unlink()
        picking.action_confirm()
        picking.action_assign()
        picking.move_line_ids.qty_done = 10.00
        picking.action_done()
        # Cancel backorder
        picking.backorder_ids.action_cancel()
        res = self.env['ir.actions.report']._get_report_from_name(
            'stock.report_deliveryslip'
        ).render_qweb_html(picking.ids)
        self.assertNotIn("undelivered_product", str(res[0]))

    def test_picking_report_method(self):
        product = self.ProductProduct.create({
            'name': 'test01',
            'display_undelivered_in_picking': True,
            'type': 'product',
        })
        product2 = self.ProductProduct.create({
            'name': 'test02',
            'display_undelivered_in_picking': True,
            'type': 'product',
        })
        self.StockQuant.create({
            'product_id': product.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'quantity': 2000,
        })
        picking_form = Form(self.StockPicking)
        picking_form.picking_type_id = self.picking_type_out
        picking_form.partner_id = self.partner_display
        with picking_form.move_ids_without_package.new() as line:
            line.product_id = product
            line.product_uom_qty = 50.00
        with picking_form.move_ids_without_package.new() as line:
            line.product_id = product2
            line.product_uom_qty = 20.00
        picking = picking_form.save()

        picking.action_confirm()
        picking.action_assign()
        picking.move_line_ids.qty_done = 10.00
        picking.action_done()
        # Cancel backorder
        picking.backorder_ids.action_cancel()

        # Empty setting method field
        picking.company_id.undelivered_product_slip_report_method = False
        res = self.env['ir.actions.report']._get_report_from_name(
            'stock.report_deliveryslip'
        ).render_qweb_html(picking.ids)
        self.assertIn("test02", str(res[0]))

        # Print all undelivered lines, partial and completely lines
        picking.company_id.undelivered_product_slip_report_method = 'all'
        res = self.env['ir.actions.report']._get_report_from_name(
            'stock.report_deliveryslip'
        ).render_qweb_html(picking.ids)
        self.assertIn("test02", str(res[0]))

        # Print only partial undelivered lines
        picking.company_id.\
            undelivered_product_slip_report_method = 'partially_undelivered'
        res = self.env['ir.actions.report']._get_report_from_name(
            'stock.report_deliveryslip'
        ).render_qweb_html(picking.ids)
        self.assertNotIn("test02", str(res[0]))

        # Print only completely undelivered lines
        picking.company_id.\
            undelivered_product_slip_report_method = 'completely_undelivered'
        res = self.env['ir.actions.report']._get_report_from_name(
            'stock.report_deliveryslip'
        ).render_qweb_html(picking.ids)
        self.assertNotIn("partially_undelivered_line", str(res[0]))
