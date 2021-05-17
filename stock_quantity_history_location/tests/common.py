# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _create_stock_move(self, location_dest_id, qty):
        move = self.env["stock.move"].create(
            {
                "name": "Stock move in",
                "location_id": self.supplier_location.id,
                "location_dest_id": location_dest_id.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": qty,
            }
        )
        move._action_confirm()
        move._action_assign()
        move_line = move.move_line_ids[0]
        move_line.qty_done = qty
        move._action_done()
        return move
