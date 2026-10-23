# Copyright 2020 Tecnativa - David Vidal
# Copyright 2026 FactorLibre
from unittest.mock import patch

from odoo.tests import Form

from odoo.addons.stock_picking_report_valued.tests.test_stock_picking_valued import (
    TestStockPickingValued,
)

from ..models.stock_move import StockMove

MOVE_LINE_LOGGER = (
    "odoo.addons.stock_picking_report_valued_sale_mrp.models.stock_move_line"
)


class TestStockPickingValuedMrp(TestStockPickingValued):
    @classmethod
    def setUpClass(cls):
        """We want to run parent class tests again to ensure everything
        works as expected even if no kits are present"""
        super().setUpClass()
        cls.res_partner = cls.env["res.partner"]
        cls.product_product = cls.env["product.product"]
        cls.product_kit = cls.product_product.create(
            {"name": "Product test 1", "type": "consu"}
        )
        cls.product_kit_comp_1 = cls.product_product.create(
            {"name": "Product Component 1", "type": "product"}
        )
        cls.product_kit_comp_2 = cls.product_product.create(
            {"name": "Product Component 2", "type": "product"}
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
        cls.components_per_kit = {
            cls.product_kit_comp_1: 2.0,
            cls.product_kit_comp_2: 4.0,
        }
        cls.product_2 = cls.product_product.create(
            {"name": "Product test 2", "type": "product"}
        )
        (
            cls.sale_order_3,
            cls.order_line,
            cls.order_out_picking,
        ) = cls._create_sale_order_with_lines(
            product=cls.product_kit,
            quantity=5,
            price_unit=29.9,
            tax=cls.tax10,
        )

    @classmethod
    def _create_sale_order_with_lines(cls, product, quantity, price_unit, tax=None):
        """Create a sale order with a single line, confirm it, and return
        the sale order, filtered order line, and picking."""
        order_form = Form(cls.env["sale.order"])
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = product
            line_form.product_uom_qty = quantity
            line_form.price_unit = price_unit
            line_form.tax_id.clear()
            if tax:
                line_form.tax_id.add(tax)
        sale_order = order_form.save()
        sale_order.action_confirm()
        order_line = sale_order.order_line.filtered(lambda r: r.product_id == product)
        picking = sale_order.picking_ids[0] if sale_order.picking_ids else None
        return sale_order, order_line, picking

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_kit_order(self, qty, extra_lines=None):
        """Sale order of ``qty`` kits (negative ``qty`` = return), confirmed."""
        lines = [
            (
                0,
                0,
                {
                    "product_id": self.product_kit.id,
                    "product_uom_qty": qty,
                    "price_unit": 29.9,
                    "tax_id": [(6, 0, self.tax10.ids)],
                },
            )
        ]
        lines += extra_lines or []
        order = self.env["sale.order"].create(
            {"partner_id": self.partner.id, "order_line": lines}
        )
        order.action_confirm()
        return order

    def _set_quantity_done(self, picking, factor=1.0):
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty * factor

    def _deliver(self, picking):
        self._set_quantity_done(picking)
        picking.button_validate()

    def _create_kit_return(self, origin_picking, qty=1):
        """Return of ``qty`` kits: sale order with a negative line, which the
        core turns into an incoming picking. Every component move is linked
        to the outgoing move it returns, as return flows do."""
        order = self._create_kit_order(-qty)
        picking = order.picking_ids
        self.assertEqual(len(picking), 1)
        self.assertEqual(picking.location_id.usage, "customer")
        for move in picking.move_ids:
            origin_move = origin_picking.move_ids.filtered(
                lambda m, move=move: m.product_id == move.product_id
            )[:1]
            self.assertTrue(origin_move)
            move.origin_returned_move_id = origin_move
        return order, picking

    def _kit_line(self, picking):
        """The kit line of ``picking``. The picking totals are read first so
        that every move line of the picking is computed in the same batch, as
        the delivery report does."""
        self.assertIsInstance(picking.amount_untaxed, float)
        kit_line = picking.move_line_ids.filtered("phantom_line")
        self.assertEqual(len(kit_line), 1)
        return kit_line

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_01_picking_confirmed(self):
        for line in self.order_out_picking.move_ids:
            line.quantity_done = line.product_uom_qty
        self.order_out_picking.button_validate()
        self.assertAlmostEqual(self.order_out_picking.amount_untaxed, 149.5)
        self.assertAlmostEqual(self.order_out_picking.amount_tax, 14.95)
        self.assertAlmostEqual(self.order_out_picking.amount_total, 164.45)
        # Run the report to detect hidden errors
        self.env["ir.actions.report"]._render_qweb_html(
            self.env.ref("stock.action_report_delivery"), self.order_out_picking.ids
        )

    @classmethod
    def _create_sale_order_for_kits(cls, qty):
        """Create a new sale order for the configured kit product."""
        return cls._create_sale_order_with_lines(
            product=cls.product_kit,
            quantity=qty,
            price_unit=29.9,
        )

    def _validate_picking(self, picking):
        picking.action_assign()
        for line in picking.move_ids:
            line.quantity_done = line.product_uom_qty
        picking.button_validate()

    def _return_picking(self, picking, quantity_factor=1.0):
        """Return a picking, optionally only a fraction of it, and validate
        the resulting return picking."""
        return_wiz = Form(
            self.env["stock.return.picking"].with_context(
                active_id=picking.id,
                active_model="stock.picking",
            )
        ).save()
        if quantity_factor != 1.0:
            for line in return_wiz.product_return_moves:
                line.quantity = line.move_id.product_uom_qty * quantity_factor
        return_picking = self.env["stock.picking"].browse(
            return_wiz.create_returns()["res_id"]
        )
        self._validate_picking(return_picking)
        return return_picking

    def _assert_components_per_kit(self, picking):
        """Every component of the picking must expose its kit ratio."""
        kit_lines = picking.move_line_ids.filtered("phantom_product_id")
        self.assertTrue(kit_lines)
        expected_per_kit = {
            self.product_kit_comp_1.id: 2.0,
            self.product_kit_comp_2.id: 4.0,
        }
        for sale_line in kit_lines.mapped("sale_line"):
            move_lines = kit_lines.filtered(lambda x: x.sale_line == sale_line)
            phantom_line = move_lines[:1]
            if not phantom_line:
                continue
            move = phantom_line.move_id
            expected = expected_per_kit[move.product_id.id]
            got = move._get_components_per_kit()
            self.assertEqual(
                got,
                expected,
                f"_get_components_per_kit returned {got} but expected {expected} "
                f"for component {move.product_id.display_name}",
            )

    def test_02_get_components_per_kit_return_redelivery(self):
        """Cancel + re-confirm adds a second delivery (#451): the ratio must
        not double."""
        sale, _so_line, picking = self._create_sale_order_for_kits(qty=2)
        self._validate_picking(picking)
        self._return_picking(picking)
        sale._action_cancel()
        sale.action_draft()
        sale.action_confirm()
        redelivery = sale.picking_ids.filtered(
            lambda p: p.state not in ("done", "cancel")
        )
        self.assertTrue(redelivery)
        self._validate_picking(redelivery[0])
        self._assert_components_per_kit(redelivery[0])

    def test_03_get_components_per_kit_return_of_return(self):
        """The usual redelivery is to return the return: the ratio stays."""
        _sale, _so_line, picking = self._create_sale_order_for_kits(qty=2)
        self._validate_picking(picking)
        return_picking = self._return_picking(picking)
        redelivery = self._return_picking(return_picking)
        self._assert_components_per_kit(redelivery)

    def test_04_get_components_per_kit_partial_return(self):
        """A partial return must not zero the ratio."""
        _sale, _so_line, picking = self._create_sale_order_for_kits(qty=2)
        self._validate_picking(picking)
        self._return_picking(picking, quantity_factor=0.5)
        self._assert_components_per_kit(picking)

    def test_05_partial_delivery(self):
        """2 of the 5 kits done: the picking is valued as 2 kits."""
        self._set_quantity_done(self.order_out_picking, factor=0.4)
        kit_line = self._kit_line(self.order_out_picking)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, 2.0)
        self.assertAlmostEqual(kit_line.sale_price_subtotal, 59.8)
        self.assertAlmostEqual(self.order_out_picking.amount_untaxed, 59.8)

    def test_06_return_full_pack(self):
        """Returning a delivered kit through a negative sale line: no
        ZeroDivisionError, and the kit is valued as 1 positive unit."""
        self._deliver(self.order_out_picking)
        _order, return_picking = self._create_kit_return(self.order_out_picking)
        self._deliver(return_picking)
        kit_line = self._kit_line(return_picking)
        expected = self.components_per_kit[kit_line.product_id]
        self.assertAlmostEqual(kit_line.move_id._get_components_per_kit(), expected)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, 1.0)
        self.assertAlmostEqual(kit_line.sale_price_subtotal, 29.9)
        self.assertAlmostEqual(kit_line.sale_price_total, 32.89)
        self.assertAlmostEqual(return_picking.amount_untaxed, 29.9)
        redundant = return_picking.move_line_ids - kit_line
        self.assertTrue(redundant)
        self.assertFalse(any(redundant.mapped("sale_price_subtotal")))

    def test_07_return_one_of_two(self):
        """Two kits sold, one returned: the return is valued as 1 kit."""
        order = self._create_kit_order(2)
        self._deliver(order.picking_ids)
        _return_order, return_picking = self._create_kit_return(order.picking_ids)
        self._deliver(return_picking)
        kit_line = self._kit_line(return_picking)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, 1.0)
        self.assertAlmostEqual(kit_line.sale_price_subtotal, 29.9)
        self.assertAlmostEqual(return_picking.amount_untaxed, 29.9)

    def test_08_zero_components_logs(self):
        """When the components per kit cannot be determined the valuation
        does not crash: quantity 0 and a warning in the log."""
        self._set_quantity_done(self.order_out_picking)
        with patch.object(
            StockMove, "_get_components_per_kit", return_value=0
        ), self.assertLogs(MOVE_LINE_LOGGER, level="WARNING") as log:
            kit_line = self._kit_line(self.order_out_picking)
            self.assertAlmostEqual(kit_line.phantom_delivered_qty, 0.0)
            self.assertAlmostEqual(kit_line.sale_price_subtotal, 0.0)
        self.assertIn("components per kit could not be determined", log.output[0])

    def test_09_sale_line_qty_zero(self):
        """A kit sale line edited to 0 does not divide by zero."""
        self._set_quantity_done(self.order_out_picking)
        self.order_line.product_uom_qty = 0
        self.assertEqual(
            self.order_out_picking.move_ids[:1]._get_components_per_kit(), 0
        )
        with self.assertLogs(MOVE_LINE_LOGGER, level="WARNING"):
            kit_line = self._kit_line(self.order_out_picking)
            self.assertAlmostEqual(kit_line.phantom_delivered_qty, 0.0)

    def test_10_kit_detection_unchanged(self):
        """Kit lines are still detected and plain lines still valued by the
        base module in a mixed picking."""
        order = self._create_kit_order(
            1,
            extra_lines=[
                (
                    0,
                    0,
                    {
                        "product_id": self.product_2.id,
                        "product_uom_qty": 3,
                        "price_unit": 10.0,
                        "tax_id": [(6, 0, self.tax10.ids)],
                    },
                )
            ],
        )
        picking = order.picking_ids
        self._set_quantity_done(picking)
        self.assertIsInstance(picking.amount_untaxed, float)
        kit_lines = picking.move_line_ids.filtered(
            lambda l: l.product_id in self.components_per_kit
        )
        plain_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_2
        )
        self.assertEqual(len(kit_lines), 2)
        self.assertEqual(kit_lines.mapped("phantom_product_id"), self.product_kit)
        self.assertFalse(plain_line.phantom_product_id)
        self.assertEqual(len(kit_lines.filtered("phantom_line")), 1)
        self.assertAlmostEqual(sum(kit_lines.mapped("sale_price_subtotal")), 29.9)
        self.assertAlmostEqual(plain_line.sale_price_subtotal, 30.0)
        self.assertAlmostEqual(picking.amount_untaxed, 59.9)

    def test_11_return_of_return(self):
        """The returned kit sent back to the customer with the standard
        return wizard hangs from the same negative sale line: it must not be
        counted as demand, so the return still values 1 kit, not half."""
        self._deliver(self.order_out_picking)
        _order, return_picking = self._create_kit_return(self.order_out_picking)
        self._deliver(return_picking)
        wizard = Form(
            self.env["stock.return.picking"].with_context(
                active_id=return_picking.id, active_model="stock.picking"
            )
        ).save()
        send_back = self.env["stock.picking"].browse(wizard.create_returns()["res_id"])
        self.assertEqual(send_back.move_ids.mapped("sale_line_id"), _order.order_line)
        self._deliver(send_back)
        kit_line = self._kit_line(return_picking)
        expected = self.components_per_kit[kit_line.product_id]
        self.assertAlmostEqual(kit_line.move_id._get_components_per_kit(), expected)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, 1.0)
        self.assertAlmostEqual(return_picking.amount_untaxed, 29.9)

    def test_12_return_several_kits(self):
        """A negative sale line returning more than one kit values them all."""
        order = self._create_kit_order(3)
        self._deliver(order.picking_ids)
        _return_order, return_picking = self._create_kit_return(
            order.picking_ids, qty=3
        )
        self._deliver(return_picking)
        kit_line = self._kit_line(return_picking)
        expected = self.components_per_kit[kit_line.product_id]
        self.assertAlmostEqual(kit_line.move_id._get_components_per_kit(), expected)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, 3.0)
        self.assertAlmostEqual(kit_line.sale_price_subtotal, 89.7)
        self.assertAlmostEqual(return_picking.amount_untaxed, 89.7)
