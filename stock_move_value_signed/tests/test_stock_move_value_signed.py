# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.stock_account.tests.common import TestStockValuationCommon

from ..hooks import _fill_value_signed


class TestStockMoveValueSigned(TestStockValuationCommon):
    """Signed value of the stock moves."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shelf_location = cls.env["stock.location"].create(
            {"name": "Shelf", "location_id": cls.stock_location.id}
        )

    def test_value_signed_in(self):
        """A receipt has a positive signed value."""
        move = self._make_in_move(self.product_fifo, 10, unit_cost=5)
        self.assertEqual(move.value, 50)
        self.assertEqual(move.value_signed, 50)

    def test_value_signed_out(self):
        """A delivery has a negative signed value."""
        self._make_in_move(self.product_fifo, 10, unit_cost=5)
        move = self._make_out_move(self.product_fifo, 4)
        self.assertEqual(move.value, 20)
        self.assertEqual(move.value_signed, -20)

    def test_value_signed_internal(self):
        """An internal transfer has no signed value."""
        self._make_in_move(self.product_fifo, 10, unit_cost=5)
        move = self._make_out_move(
            self.product_fifo, 4, location_dest_id=self.shelf_location.id
        )
        self.assertEqual(move.value_signed, 0)

    def test_value_signed_fill(self):
        """The installation fills the signed value like the computation.

        Scenario:
            1. Receive 10 units at 5, deliver 4 of them and move 2 to a shelf.
            2. Fill the signed value of all the moves as the installation does.
        Expected:
            - The receipt, delivery and internal transfer keep their signed
              values: 50, -20 and 0.
        """
        moves = (
            self._make_in_move(self.product_fifo, 10, unit_cost=5)
            | self._make_out_move(self.product_fifo, 4)
            | self._make_out_move(
                self.product_fifo, 2, location_dest_id=self.shelf_location.id
            )
        )
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE stock_move SET value_signed = NULL WHERE id IN %s",
            (tuple(moves.ids),),
        )
        _fill_value_signed(self.env.cr)
        moves.invalidate_recordset(["value_signed"])
        self.assertEqual(moves.mapped("value_signed"), [50, -20, 0])
