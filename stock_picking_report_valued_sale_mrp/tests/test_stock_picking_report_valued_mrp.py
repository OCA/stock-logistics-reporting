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

    def _create_kit_order(
        self, qty, extra_lines=None, product=None, uom=None, price_unit=29.9, taxes=None
    ):
        """Sale order of ``qty`` kits (negative ``qty`` = return), confirmed."""
        product = product or self.product_kit
        lines = [
            (
                0,
                0,
                {
                    "product_id": product.id,
                    "product_uom": (uom or product.uom_id).id,
                    "product_uom_qty": qty,
                    "price_unit": price_unit,
                    "tax_id": [(6, 0, (self.tax10 if taxes is None else taxes).ids)],
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

    def _deliver_partially(self, picking, factor, backorder=True):
        """Validate ``factor`` of the picking, with or without a backorder for
        the rest. Return the backorder, if any."""
        self._set_quantity_done(picking, factor)
        action = picking.button_validate()
        wizard = Form(
            self.env[action["res_model"]].with_context(**action["context"])
        ).save()
        if backorder:
            wizard.process()
        else:
            wizard.process_cancel_backorder()
        return picking.backorder_ids

    def _create_kit_bom(self, product, lines, product_qty=1.0):
        """Kit BoM of ``product`` with ``lines`` as (component, qty)."""
        return self.env["mrp.bom"].create(
            {
                "product_id": product.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "type": "phantom",
                "product_qty": product_qty,
                "bom_line_ids": [
                    (0, 0, {"product_id": component.id, "product_qty": qty})
                    for component, qty in lines
                ],
            }
        )

    def _assert_one_kit(self, picking, expected_per_kit=None):
        """The picking is valued as 1 kit and, when given, each component
        exposes its ratio."""
        kit_line = self._kit_line(picking)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, 1.0)
        self.assertAlmostEqual(kit_line.sale_price_subtotal, 29.9)
        for move in picking.move_ids:
            expected = (expected_per_kit or self.components_per_kit)[move.product_id]
            self.assertAlmostEqual(move._get_components_per_kit(), expected)

    def _create_tax(self, amount, price_include):
        return self.env["account.tax"].create(
            {
                "name": f"Tax {amount}% {'included' if price_include else ''}",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": amount,
                "price_include": price_include,
            }
        )

    def _assert_kit_amounts(self, picking, subtotal, tax, total):
        kit_line = self._kit_line(picking)
        self.assertAlmostEqual(kit_line.sale_price_subtotal, subtotal)
        self.assertAlmostEqual(kit_line.sale_price_tax, tax)
        self.assertAlmostEqual(kit_line.sale_price_total, total)
        return kit_line

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

    def test_13_qty_increase_after_full_return(self):
        """1 kit delivered, the line raised to 2 and the first delivery fully
        returned: the second delivery is valued as 1 kit, not 2."""
        order = self._create_kit_order(1)
        first_picking = order.picking_ids
        self._deliver(first_picking)
        # The core recomputes the price from the pricelist on a qty change
        order.order_line.write({"product_uom_qty": 2, "price_unit": 29.9})
        second_picking = order.picking_ids - first_picking
        self.assertEqual(len(second_picking), 1)
        self._return_picking(first_picking)
        self._deliver(second_picking)
        self._assert_one_kit(second_picking)

    def test_14_backorder_after_full_return(self):
        """2 kits delivered in two pickings and the first one fully returned:
        the backorder is valued as 1 kit, not 2."""
        order = self._create_kit_order(2)
        picking = order.picking_ids
        backorder = self._deliver_partially(picking, 0.5)
        self._return_picking(picking)
        self._deliver(backorder)
        self._assert_one_kit(backorder)

    def test_15_negative_line_return_then_backorder(self):
        """2 kits delivered in two pickings and the first one returned from a
        negative sale line: the backorder is valued as 1 kit."""
        order = self._create_kit_order(2)
        picking = order.picking_ids
        backorder = self._deliver_partially(picking, 0.5)
        _return_order, return_picking = self._create_kit_return(picking)
        self._deliver(return_picking)
        self._deliver(backorder)
        self._assert_one_kit(backorder)

    def test_16_components_per_kit_without_bom_line(self):
        """A component move without BoM line keeps the demand ratio."""
        order = self._create_kit_order(2)
        picking = order.picking_ids
        self._deliver(picking)
        picking.move_ids.bom_line_id = False
        for move in picking.move_ids:
            self.assertAlmostEqual(
                move._get_components_per_kit(),
                self.components_per_kit[move.product_id],
            )

    def test_17_kit_price_include_tax(self):
        """Kit at 10.91 with 10% VAT included: the included tax is extracted
        once (9.92 / 0.99 / 10.91), not twice (9.02 / 0.90 / 9.92)."""
        order = self._create_kit_order(
            1, price_unit=10.91, taxes=self._create_tax(10, True)
        )
        picking = order.picking_ids
        self._deliver(picking)
        self._assert_kit_amounts(picking, 9.92, 0.99, 10.91)
        self.assertAlmostEqual(picking.amount_untaxed, 9.92)
        self.assertAlmostEqual(picking.amount_total, 10.91)

    def test_18_kit_price_include_igic(self):
        """Kit at 10.91 with 3% IGIC included: 10.59 / 0.32 / 10.91."""
        order = self._create_kit_order(
            1, price_unit=10.91, taxes=self._create_tax(3, True)
        )
        picking = order.picking_ids
        self._deliver(picking)
        self._assert_kit_amounts(picking, 10.59, 0.32, 10.91)

    def test_19_kit_tax_excluded_and_exempt_unchanged(self):
        """Tax excluded and no tax: the kit is valued as its sale line."""
        for taxes, tax, total in (
            (self.tax10, 2.99, 32.89),
            (self.env["account.tax"], 0.0, 29.9),
        ):
            order = self._create_kit_order(1, taxes=taxes)
            picking = order.picking_ids
            self._deliver(picking)
            self._assert_kit_amounts(picking, 29.9, tax, total)

    def test_20_kit_and_normal_line_price_include(self):
        """Kit and a plain product with VAT included: the plain line is valued
        as its sale line and the kit without the tax extracted twice."""
        tax = self._create_tax(10, True)
        order = self._create_kit_order(
            1,
            price_unit=10.91,
            taxes=tax,
            extra_lines=[
                (
                    0,
                    0,
                    {
                        "product_id": self.product_2.id,
                        "product_uom_qty": 3,
                        "price_unit": 10.0,
                        "tax_id": [(6, 0, tax.ids)],
                    },
                )
            ],
        )
        picking = order.picking_ids
        self._deliver(picking)
        self._assert_kit_amounts(picking, 9.92, 0.99, 10.91)
        plain_sale_line = order.order_line.filtered(
            lambda l: l.product_id == self.product_2
        )
        plain_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_2
        )
        self.assertAlmostEqual(
            plain_line.sale_price_subtotal, plain_sale_line.price_subtotal
        )
        self.assertAlmostEqual(plain_line.sale_price_total, plain_sale_line.price_total)

    def test_21_kit_price_include_partial_delivery(self):
        """2 kits with VAT included, 1 per picking: each picking values 1 kit
        without the tax extracted twice."""
        order = self._create_kit_order(
            2, price_unit=10.91, taxes=self._create_tax(10, True)
        )
        picking = order.picking_ids
        backorder = self._deliver_partially(picking, 0.5)
        self._deliver(backorder)
        self._assert_kit_amounts(picking, 9.92, 0.99, 10.91)
        self._assert_kit_amounts(backorder, 9.92, 0.99, 10.91)

    def test_22_split_delivery_without_return(self):
        """2 kits delivered in two pickings, no return: 1 kit in each."""
        order = self._create_kit_order(2)
        picking = order.picking_ids
        backorder = self._deliver_partially(picking, 0.5)
        self._deliver(backorder)
        self._assert_one_kit(picking)
        self._assert_one_kit(backorder)

    def test_23_bom_qty_and_repeated_component(self):
        """A BoM making 2 kits with the same component in two lines; backorder
        after a full return: the backorder is valued as 1 kit."""
        kit = self.product_product.create({"name": "Kit x2", "type": "consu"})
        self._create_kit_bom(
            kit,
            [
                (self.product_kit_comp_1, 2),
                (self.product_kit_comp_1, 2),
                (self.product_kit_comp_2, 4),
            ],
            product_qty=2,
        )
        order = self._create_kit_order(2, product=kit)
        picking = order.picking_ids
        backorder = self._deliver_partially(picking, 0.5)
        self._return_picking(picking)
        self._deliver(backorder)
        self._assert_one_kit(
            backorder,
            {self.product_kit_comp_1: 2.0, self.product_kit_comp_2: 2.0},
        )

    def test_24_nested_kit(self):
        """A kit with an inner kit, backorder after a full return: the components of
        the inner kit point to its BoM, and the backorder is still valued as
        1 kit."""
        inner_kit = self.product_product.create({"name": "Inner kit", "type": "consu"})
        self._create_kit_bom(inner_kit, [(self.product_kit_comp_2, 3)])
        kit = self.product_product.create({"name": "Outer kit", "type": "consu"})
        self._create_kit_bom(kit, [(self.product_kit_comp_1, 2), (inner_kit, 1)])
        order = self._create_kit_order(2, product=kit)
        picking = order.picking_ids
        backorder = self._deliver_partially(picking, 0.5)
        self._return_picking(picking)
        self._deliver(backorder)
        self._assert_one_kit(
            backorder,
            {self.product_kit_comp_1: 2.0, self.product_kit_comp_2: 3.0},
        )

    def test_25_partial_delivery_without_backorder(self):
        """1 of 2 kits delivered and the rest cancelled (no backorder): the
        picking is valued as 1 kit, not 2."""
        order = self._create_kit_order(2)
        picking = order.picking_ids
        self.assertFalse(self._deliver_partially(picking, 0.5, backorder=False))
        self._assert_one_kit(picking)

    def test_26_two_step_delivery(self):
        """Pick + ship: only the ship moves hang from the sale line. The
        backorder of the ship picking after a full return values 1 kit."""
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        warehouse.delivery_steps = "pick_ship"
        order = self._create_kit_order(2)
        pick = order.picking_ids.filtered(
            lambda p: p.picking_type_id == warehouse.pick_type_id
        )
        ship = order.picking_ids.filtered(
            lambda p: p.picking_type_id == warehouse.out_type_id
        )
        self.assertTrue(pick and ship)
        self.assertFalse(pick.move_ids.sale_line_id)
        self._deliver(pick)
        backorder = self._deliver_partially(ship, 0.5)
        self._return_picking(ship)
        self._deliver(backorder)
        self._assert_one_kit(backorder)

    def test_27_kit_sold_in_other_uom(self):
        """A kit sold by the dozen: the ratio is per dozen and the backorder
        after a full return is valued as 1 dozen."""
        dozen = self.env.ref("uom.product_uom_dozen")
        order = self._create_kit_order(2, uom=dozen)
        picking = order.picking_ids
        backorder = self._deliver_partially(picking, 0.5)
        self._return_picking(picking)
        self._deliver(backorder)
        self._assert_one_kit(
            backorder,
            {self.product_kit_comp_1: 24.0, self.product_kit_comp_2: 48.0},
        )

    def test_28_component_in_kit_and_inner_kit(self):
        """The same component in the kit and in its inner kit: both lines are
        added up; backorder after a full return."""
        inner_kit = self.product_product.create({"name": "Inner kit", "type": "consu"})
        self._create_kit_bom(
            inner_kit,
            [(self.product_kit_comp_1, 1), (self.product_kit_comp_2, 3)],
        )
        kit = self.product_product.create({"name": "Outer kit", "type": "consu"})
        self._create_kit_bom(kit, [(self.product_kit_comp_1, 2), (inner_kit, 1)])
        order = self._create_kit_order(2, product=kit)
        picking = order.picking_ids
        backorder = self._deliver_partially(picking, 0.5)
        self._return_picking(picking)
        self._deliver(backorder)
        self._assert_one_kit(
            backorder,
            {self.product_kit_comp_1: 3.0, self.product_kit_comp_2: 3.0},
        )

    def test_29_new_bom_after_sale(self):
        """A new BoM replaces the kit BoM after the sale: the moves keep the
        BoM they were exploded with, so the ratio doesn't change."""
        order = self._create_kit_order(2)
        self.bom.active = False
        self._create_kit_bom(
            self.product_kit,
            [(self.product_kit_comp_1, 5), (self.product_kit_comp_2, 1)],
        )
        picking = order.picking_ids
        backorder = self._deliver_partially(picking, 0.5)
        self._return_picking(picking)
        self._deliver(backorder)
        self._assert_one_kit(backorder)

    def test_30_kit_price_include_with_discount(self):
        """Kit at 10.91 with VAT included and a 10% discount: valued from the
        discounted subtotal of the sale line (8.93 / 0.89 / 9.82)."""
        order = self._create_kit_order(
            1, price_unit=10.91, taxes=self._create_tax(10, True)
        )
        order.order_line.discount = 10
        picking = order.picking_ids
        self._deliver(picking)
        self._assert_kit_amounts(picking, 8.93, 0.89, 9.82)

    def test_31_return_price_include(self):
        """A kit with VAT included returned from a negative sale line: the
        return is valued as 1 positive kit without the tax extracted twice."""
        tax = self._create_tax(10, True)
        order = self._create_kit_order(1, price_unit=10.91, taxes=tax)
        self._deliver(order.picking_ids)
        return_order = self._create_kit_order(-1, price_unit=10.91, taxes=tax)
        return_picking = return_order.picking_ids
        for move in return_picking.move_ids:
            move.origin_returned_move_id = order.picking_ids.move_ids.filtered(
                lambda m, move=move: m.product_id == move.product_id
            )
        self._deliver(return_picking)
        kit_line = self._assert_kit_amounts(return_picking, 9.92, 0.99, 10.91)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, 1.0)

    def test_32_kit_price_include_round_globally(self):
        """With taxes rounded globally the kit amounts are the same."""
        self.env.company.tax_calculation_rounding_method = "round_globally"
        order = self._create_kit_order(
            1, price_unit=10.91, taxes=self._create_tax(10, True)
        )
        picking = order.picking_ids
        self._deliver(picking)
        kit_line = self._kit_line(picking)
        self.assertAlmostEqual(kit_line.sale_price_subtotal, 9.92)
        self.assertAlmostEqual(kit_line.sale_price_total, 10.91, delta=0.005)

    def test_33_template_bom_with_variant_line(self):
        """A kit BoM on the template with a line only for one variant, replaced
        after the sale; backorder after a full return: each variant is valued
        as 1 kit with the BoM its moves were exploded with."""
        attribute = self.env["product.attribute"].create(
            {
                "name": "Color",
                "value_ids": [(0, 0, {"name": "Red"}), (0, 0, {"name": "Blue"})],
            }
        )
        template = self.env["product.template"].create(
            {
                "name": "Kit by color",
                "type": "consu",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": attribute.id,
                            "value_ids": [(6, 0, attribute.value_ids.ids)],
                        },
                    )
                ],
            }
        )
        red_value = template.attribute_line_ids.product_template_value_ids.filtered(
            lambda v: v.name == "Red"
        )
        red = template.product_variant_ids.filtered(
            lambda p: red_value in p.product_template_attribute_value_ids
        )
        blue = template.product_variant_ids - red
        bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": template.id,
                "type": "phantom",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {"product_id": self.product_kit_comp_1.id, "product_qty": 2},
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_kit_comp_2.id,
                            "product_qty": 4,
                            "bom_product_template_attribute_value_ids": [
                                (6, 0, red_value.ids)
                            ],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_kit_comp_1.id,
                            "product_qty": 1,
                            "bom_product_template_attribute_value_ids": [
                                (6, 0, red_value.ids)
                            ],
                        },
                    ),
                ],
            }
        )
        orders = {
            variant: self._create_kit_order(2, product=variant)
            for variant in red | blue
        }
        bom.active = False
        self.env["mrp.bom"].create(
            {
                "product_tmpl_id": template.id,
                "type": "phantom",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {"product_id": self.product_kit_comp_1.id, "product_qty": 5},
                    ),
                    (
                        0,
                        0,
                        {"product_id": self.product_kit_comp_2.id, "product_qty": 1},
                    ),
                ],
            }
        )
        for variant, expected in (
            (red, {self.product_kit_comp_1: 3.0, self.product_kit_comp_2: 4.0}),
            (blue, {self.product_kit_comp_1: 2.0}),
        ):
            picking = orders[variant].picking_ids
            self.assertEqual(
                picking.move_ids.product_id,
                self.product_product.concat(*expected.keys()),
            )
            backorder = self._deliver_partially(picking, 0.5)
            self._return_picking(picking)
            self._deliver(backorder)
            self._assert_one_kit(backorder, expected)

    def test_34_kit_with_a_consumable_component(self):
        """A kit of a storable and a consumable component (a kit of only
        consumables isn't a kit for the core, see product.get_components);
        backorder after a full return: the backorder is valued as 1 kit."""
        consumable = self.product_product.create(
            {"name": "Consumable component", "type": "consu"}
        )
        kit = self.product_product.create({"name": "Mixed kit", "type": "consu"})
        self._create_kit_bom(kit, [(self.product_kit_comp_1, 2), (consumable, 3)])
        order = self._create_kit_order(2, product=kit)
        picking = order.picking_ids
        backorder = self._deliver_partially(picking, 0.5)
        self._return_picking(picking)
        self._deliver(backorder)
        self._assert_one_kit(backorder, {self.product_kit_comp_1: 2.0, consumable: 3.0})

    def _assert_kits(self, picking, kits, expected_per_kit):
        """The picking is valued as ``kits`` kits and each component exposes
        its ratio."""
        kit_line = self._kit_line(picking)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, kits)
        self.assertAlmostEqual(kit_line.sale_price_subtotal, kits * 29.9)
        for move in picking.move_ids:
            self.assertAlmostEqual(
                move._get_components_per_kit(), expected_per_kit[move.product_id]
            )

    def test_35_inner_kit_bom_making_several(self):
        """An inner kit BoM making 3 units: the components per kit are the
        ones of the moves, rounded as the core rounds them for the line."""
        inner_kit = self.product_product.create({"name": "Inner kit", "type": "consu"})
        self._create_kit_bom(inner_kit, [(self.product_kit_comp_2, 1)], product_qty=3)
        kit = self.product_product.create({"name": "Outer kit", "type": "consu"})
        self._create_kit_bom(kit, [(self.product_kit_comp_1, 2), (inner_kit, 1)])
        for kits, comp_2_per_kit in ((3, 1 / 3), (1, 0.34)):
            order = self._create_kit_order(kits, product=kit)
            picking = order.picking_ids
            self._deliver(picking)
            self._assert_kits(
                picking,
                kits,
                {
                    self.product_kit_comp_1: 2.0,
                    self.product_kit_comp_2: comp_2_per_kit,
                },
            )

    def test_36_half_component_in_whole_units(self):
        """Half a component per kit with a UoM rounded to whole units: the
        core rounds the component of the line up, and so does the ratio."""
        self.env.ref("uom.product_uom_unit").rounding = 1.0
        kit = self.product_product.create({"name": "Kit of halves", "type": "consu"})
        self._create_kit_bom(
            kit, [(self.product_kit_comp_1, 0.5), (self.product_kit_comp_2, 4)]
        )
        for kits, comp_1_per_kit in ((10, 0.5), (1, 1.0)):
            order = self._create_kit_order(kits, product=kit)
            picking = order.picking_ids
            self._deliver(picking)
            self._assert_kits(
                picking,
                kits,
                {
                    self.product_kit_comp_1: comp_1_per_kit,
                    self.product_kit_comp_2: 4.0,
                },
            )

    def test_37_nested_kit_outer_bom_replaced(self):
        """The outer BoM of a nested kit replaced after the sale: the
        components of the inner kit take it from the other moves of the
        picking, not from the new BoM."""
        inner_kit = self.product_product.create({"name": "Inner kit", "type": "consu"})
        self._create_kit_bom(inner_kit, [(self.product_kit_comp_2, 3)])
        kit = self.product_product.create({"name": "Outer kit", "type": "consu"})
        bom = self._create_kit_bom(kit, [(self.product_kit_comp_1, 2), (inner_kit, 1)])
        order = self._create_kit_order(2, product=kit)
        bom.active = False
        self._create_kit_bom(kit, [(self.product_kit_comp_1, 2), (inner_kit, 2)])
        picking = order.picking_ids
        self._deliver(picking)
        self._assert_kits(
            picking,
            2.0,
            {self.product_kit_comp_1: 2.0, self.product_kit_comp_2: 3.0},
        )

    def test_38_only_inner_kits_outer_bom_replaced(self):
        """A kit made only of an inner kit, its BoM replaced after the sale:
        no move tells the kit BoM, so the demand ratio is used instead of the
        new BoM."""
        inner_kit = self.product_product.create({"name": "Inner kit", "type": "consu"})
        self._create_kit_bom(
            inner_kit, [(self.product_kit_comp_1, 2), (self.product_kit_comp_2, 3)]
        )
        kit = self.product_product.create({"name": "Outer kit", "type": "consu"})
        bom = self._create_kit_bom(kit, [(inner_kit, 1)])
        order = self._create_kit_order(2, product=kit)
        bom.active = False
        self._create_kit_bom(kit, [(inner_kit, 2)])
        picking = order.picking_ids
        self._deliver(picking)
        self._assert_kits(
            picking,
            2.0,
            {self.product_kit_comp_1: 2.0, self.product_kit_comp_2: 3.0},
        )

    def test_39_bom_line_replaced_after_sale(self):
        """A BoM line deleted and created again after the sale: its moves lose
        the BoM line, so the demand ratio is used instead of the new line."""
        kit = self.product_product.create({"name": "Edited kit", "type": "consu"})
        bom = self._create_kit_bom(
            kit, [(self.product_kit_comp_1, 2), (self.product_kit_comp_2, 4)]
        )
        order = self._create_kit_order(2, product=kit)
        bom.bom_line_ids.filtered(
            lambda line: line.product_id == self.product_kit_comp_1
        ).unlink()
        bom.bom_line_ids = [
            (0, 0, {"product_id": self.product_kit_comp_1.id, "product_qty": 3})
        ]
        picking = order.picking_ids
        self.assertFalse(
            picking.move_ids.filtered(
                lambda m: m.product_id == self.product_kit_comp_1
            ).bom_line_id
        )
        self._deliver(picking)
        self._assert_kits(
            picking,
            2.0,
            {self.product_kit_comp_1: 2.0, self.product_kit_comp_2: 4.0},
        )

    def test_40_half_component_in_whole_units_qty_increase(self):
        """Half a component per kit with a UoM rounded to whole units and the
        line raised after the first delivery: each explosion rounds up on its
        own, so the BoM of the whole line doesn't match the moves and the
        demand ratio is used instead. Each delivery is valued as 1 kit."""
        self.env.ref("uom.product_uom_unit").rounding = 1.0
        kit = self.product_product.create({"name": "Kit of halves", "type": "consu"})
        self._create_kit_bom(
            kit, [(self.product_kit_comp_1, 0.5), (self.product_kit_comp_2, 4)]
        )
        order = self._create_kit_order(1, product=kit)
        first_picking = order.picking_ids
        self._deliver(first_picking)
        order.order_line.write({"product_uom_qty": 2, "price_unit": 29.9})
        second_picking = order.picking_ids - first_picking
        self._deliver(second_picking)
        for picking in first_picking | second_picking:
            self._assert_kits(
                picking,
                1.0,
                {self.product_kit_comp_1: 1.0, self.product_kit_comp_2: 4.0},
            )

    def test_41_half_component_in_whole_units_backorder_after_return(self):
        """Half a component per kit with a UoM rounded to whole units, 4 kits
        delivered in two pickings and the first one fully returned: the line
        was exploded once, so its BoM still matches the moves and the
        backorder is valued as 2 kits."""
        self.env.ref("uom.product_uom_unit").rounding = 1.0
        kit = self.product_product.create({"name": "Kit of halves", "type": "consu"})
        self._create_kit_bom(
            kit, [(self.product_kit_comp_1, 0.5), (self.product_kit_comp_2, 4)]
        )
        order = self._create_kit_order(4, product=kit)
        picking = order.picking_ids
        backorder = self._deliver_partially(picking, 0.5)
        self._return_picking(picking)
        self._deliver(backorder)
        self._assert_kits(
            backorder,
            2.0,
            {self.product_kit_comp_1: 0.5, self.product_kit_comp_2: 4.0},
        )

    def test_42_half_component_qty_increase_after_full_return(self):
        """Half a component per kit with a UoM rounded to whole units, the
        line raised after the first delivery and the first delivery fully
        returned: the rounded component can't tell the kits, so they are
        deduced from the other one and the second delivery is valued as 1 kit."""
        self.env.ref("uom.product_uom_unit").rounding = 1.0
        kit = self.product_product.create({"name": "Kit of halves", "type": "consu"})
        self._create_kit_bom(
            kit, [(self.product_kit_comp_1, 0.5), (self.product_kit_comp_2, 4)]
        )
        order = self._create_kit_order(1, product=kit)
        first_picking = order.picking_ids
        self._deliver(first_picking)
        order.order_line.write({"product_uom_qty": 2, "price_unit": 29.9})
        second_picking = order.picking_ids - first_picking
        self._return_picking(first_picking)
        self._deliver(second_picking)
        kit_line = self._kit_line(second_picking)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, 1.0)
        self.assertAlmostEqual(kit_line.sale_price_subtotal, 29.9)

    def test_43_half_component_partial_delivery_without_backorder(self):
        """Half a component per kit with a UoM rounded to whole units and 2
        of 4 kits delivered without backorder: the cancelled rest was exploded
        with the line, so the BoM still tells the components per kit."""
        self.env.ref("uom.product_uom_unit").rounding = 1.0
        kit = self.product_product.create({"name": "Kit of halves", "type": "consu"})
        self._create_kit_bom(
            kit, [(self.product_kit_comp_1, 0.5), (self.product_kit_comp_2, 4)]
        )
        order = self._create_kit_order(4, product=kit)
        picking = order.picking_ids
        self._deliver_partially(picking, 0.5, backorder=False)
        self._assert_kits(
            picking,
            2.0,
            {self.product_kit_comp_1: 0.5, self.product_kit_comp_2: 4.0},
        )

    def test_44_half_component_qty_increase_before_delivery(self):
        """Half a component per kit with a UoM rounded to whole units and the
        line raised before delivering: both explosions end up in the same
        picking, valued as 2 kits."""
        self.env.ref("uom.product_uom_unit").rounding = 1.0
        kit = self.product_product.create({"name": "Kit of halves", "type": "consu"})
        self._create_kit_bom(
            kit, [(self.product_kit_comp_1, 0.5), (self.product_kit_comp_2, 4)]
        )
        order = self._create_kit_order(1, product=kit)
        order.order_line.write({"product_uom_qty": 2, "price_unit": 29.9})
        picking = order.picking_ids
        self._deliver(picking)
        kit_line = self._kit_line(picking)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, 2.0)
        self.assertAlmostEqual(kit_line.sale_price_subtotal, 59.8)

    def test_45_bom_ratio_checked_once_per_move(self):
        """Components split in several move lines (lots, packages): the BoM
        ratio is checked once per move, not once per line, and the picking is
        still valued from the whole move."""
        order = self._create_kit_order(2)
        picking = order.picking_ids
        self._set_quantity_done(picking)
        for move in picking.move_ids:
            line = move.move_line_ids
            half = line.qty_done / 2
            line.qty_done = half
            line.copy({"move_id": move.id, "qty_done": half})
        self.assertEqual(len(picking.move_line_ids), 4)
        with patch.object(
            StockMove, "_get_components_per_kit_from_bom", return_value=0.0
        ) as from_bom:
            kit_line = self._kit_line(picking)
            self.assertAlmostEqual(kit_line.phantom_delivered_qty, 2.0)
            self.assertAlmostEqual(kit_line.sale_price_subtotal, 59.8)
        # Once per move to choose the component, and once more from
        # _get_components_per_kit on the chosen one.
        self.assertEqual(from_bom.call_count, len(picking.move_ids) + 1)

    def test_46_bom_line_qty_edited_after_sale(self):
        """Known limitation: the quantity of a BoM line edited after the sale.
        The moves still point to the edited line, so its new quantity is used
        as the components per kit: 4 components delivered with 3 per kit are
        valued as 1.33 kits instead of 2."""
        kit = self.product_product.create({"name": "Edited kit", "type": "consu"})
        bom = self._create_kit_bom(
            kit, [(self.product_kit_comp_1, 2), (self.product_kit_comp_2, 4)]
        )
        order = self._create_kit_order(2, product=kit)
        bom.bom_line_ids.filtered(
            lambda line: line.product_id == self.product_kit_comp_1
        ).product_qty = 3
        picking = order.picking_ids
        self._deliver(picking)
        kit_line = self._kit_line(picking)
        self.assertAlmostEqual(kit_line.phantom_delivered_qty, 4 / 3)
        self.assertAlmostEqual(kit_line.sale_price_subtotal, 39.87)
