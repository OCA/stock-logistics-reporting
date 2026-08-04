from lxml import etree

from odoo.fields import Command

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.stock_move_pivot_total_price.hooks import (
    _backfill_product_total_price,
    create_column_product_total_price,
)


class TestStockPivotTotalPrice(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 10.0,
            }
        )

    def _create_move(
        self, product=None, demand=0.0, quantity=0.0, product_uom=None, origin=None
    ):
        product = product or self.product
        move = self.env["stock.move"].create(
            {
                "product_id": product.id,
                "product_uom": (product_uom or product.uom_id).id,
                "product_uom_qty": demand,
                "location_id": self.supplier_location.id,
                "location_dest_id": self.stock_location.id,
                "origin": origin,
            }
        )
        if quantity:
            move.quantity = quantity
        return move

    def _create_variant(self, extras):
        attribute_lines = []
        for index, extra in enumerate(extras, start=1):
            attribute = self.env["product.attribute"].create(
                {
                    "name": f"Attribute {index}",
                    "create_variant": "always",
                    "value_ids": [
                        Command.create(
                            {
                                "name": f"Value {index}",
                                "default_extra_price": extra,
                            }
                        )
                    ],
                }
            )
            attribute_lines.append(
                Command.create(
                    {
                        "attribute_id": attribute.id,
                        "value_ids": [Command.set(attribute.value_ids.ids)],
                    }
                )
            )
        template = self.env["product.template"].create(
            {
                "name": "Variant Product",
                "type": "consu",
                "list_price": 100.0,
                "attribute_line_ids": attribute_lines,
            }
        )
        return template.product_variant_id

    def _neutral_context_price(self, product):
        return product.with_context(uom=False).lst_price

    def test_automatic_calculation_and_recomputation(self):
        move = self._create_move(demand=10.0)
        self.assertEqual(move.quantity, 0.0)
        self.assertEqual(move.product_total_price, 0.0)

        move.quantity = 10.0
        self.assertEqual(move.product_total_price, 100.0)

        move.move_line_ids.quantity = 4.0
        self.assertEqual(move.quantity, 4.0)
        self.assertEqual(move.product_total_price, 40.0)

    def test_partial_completion_and_backorder(self):
        move = self._create_move(demand=10.0, quantity=4.0)
        move.picked = True
        move._action_done()

        backorder = self.env["stock.move"].search(
            [
                ("id", "!=", move.id),
                ("product_id", "=", self.product.id),
                ("origin", "=", move.origin),
            ]
        )
        self.assertEqual(move.state, "done")
        self.assertEqual(move.quantity, 4.0)
        self.assertEqual(move.product_total_price, 40.0)
        self.assertEqual(len(backorder), 1)
        self.assertEqual(backorder.product_uom_qty, 6.0)
        self.assertEqual(
            backorder.product_total_price,
            self.product.lst_price * backorder.quantity,
        )

    def test_zero_and_canceled_moves(self):
        zero_move = self._create_move(demand=5.0)
        self.assertEqual(zero_move.product_total_price, 0.0)

        canceled_move = self._create_move(demand=3.0, quantity=3.0)
        self.assertEqual(canceled_move.product_total_price, 30.0)
        canceled_move._action_cancel()
        self.assertEqual(canceled_move.state, "cancel")
        self.assertEqual(canceled_move.quantity, 0.0)
        self.assertEqual(canceled_move.product_total_price, 0.0)

    def test_variant_price_extras(self):
        one_extra = self._create_variant([10.0])
        multiple_extras = self._create_variant([10.0, 20.0])

        one_extra_move = self._create_move(product=one_extra, demand=2.0, quantity=2.0)
        multiple_extra_move = self._create_move(
            product=multiple_extras, demand=2.0, quantity=2.0
        )

        self.assertEqual(one_extra.lst_price, 110.0)
        self.assertEqual(one_extra_move.product_total_price, 220.0)
        self.assertEqual(multiple_extras.lst_price, 130.0)
        self.assertEqual(multiple_extra_move.product_total_price, 260.0)

    def test_different_move_uom_preserves_current_basis(self):
        dozen = self.env.ref("uom.product_uom_dozen")
        self.product.uom_ids = [Command.link(dozen.id)]
        move = self._create_move(
            demand=2.0,
            quantity=2.0,
            product_uom=dozen,
        )

        self.assertEqual(move.quantity, 2.0)
        self.assertEqual(move.product_total_price, 20.0)
        self.assertEqual(
            move.product_id.uom_id._compute_quantity(
                move.quantity, move.product_uom, round=False
            ),
            2.0 / 12.0,
        )

    def test_sql_backfill_matches_orm_computation(self):
        one_extra = self._create_variant([10.0])
        multiple_extras = self._create_variant([10.0, 20.0])
        moves = (
            self._create_move(demand=5.0, quantity=5.0)
            | self._create_move(product=one_extra, demand=2.0, quantity=2.0)
            | self._create_move(product=multiple_extras, demand=2.0, quantity=2.0)
        )
        expected = {
            move.id: self._neutral_context_price(move.product_id) * move.quantity
            for move in moves
        }
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE stock_move SET product_total_price = NULL WHERE id IN %s",
            [tuple(moves.ids)],
        )

        _backfill_product_total_price(self.env.cr)
        moves.invalidate_recordset(["product_total_price"])

        for move in moves:
            self.assertEqual(move.product_total_price, expected[move.id])

    def test_existing_column_is_not_overwritten(self):
        move = self._create_move(demand=2.0, quantity=2.0)
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE stock_move SET product_total_price = %s WHERE id = %s",
            [4242.0, move.id],
        )

        create_column_product_total_price(self.env.cr)
        move.invalidate_recordset(["product_total_price"])

        self.assertEqual(move.product_total_price, 4242.0)

    def test_read_group_sums_total_price(self):
        moves = self._create_move(demand=2.0, quantity=2.0) | self._create_move(
            demand=3.0, quantity=3.0
        )

        result = self.env["stock.move"]._read_group(
            [("id", "in", moves.ids)],
            aggregates=["product_total_price:sum"],
        )

        self.assertEqual(result, [(50.0,)])

    def test_pivot_architecture_contains_total_price_measure(self):
        view = self.env["stock.move"].get_view(
            view_id=self.env.ref("stock.view_move_pivot").id,
            view_type="pivot",
        )
        arch = etree.fromstring(view["arch"])
        fields = arch.xpath("//field[@name='product_total_price']")

        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0].get("type"), "measure")
        self.assertEqual(fields[0].get("string"), "Total Price")

    def test_price_only_change_does_not_recompute_historical_total(self):
        move = self._create_move(demand=2.0, quantity=2.0)
        self.assertEqual(move.product_total_price, 20.0)

        self.product.list_price = 25.0
        self.assertEqual(move.product_total_price, 20.0)

        move.quantity = 3.0
        self.assertEqual(move.product_total_price, 75.0)
