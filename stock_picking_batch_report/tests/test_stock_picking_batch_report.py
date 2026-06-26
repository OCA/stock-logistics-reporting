# Copyright (C) 2026 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import TransactionCase


class TestStockPickingBatchReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.output_location = cls.warehouse.wh_output_stock_loc_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Batch Report Test Product",
                "type": "consu",
                "is_storable": True,
                "uom_id": cls.uom_unit.id,
            }
        )

    @classmethod
    def _create_picking(cls, picking_type, location, location_dest):
        return cls.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
            }
        )

    @classmethod
    def _create_move(cls, picking, location, location_dest):
        return cls.env["stock.move"].create(
            {
                "picking_id": picking.id,
                "product_id": cls.product.id,
                "product_uom_qty": 1.0,
                "product_uom": cls.uom_unit.id,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
            }
        )

    def test_get_out_pickings_returns_chained_destination_pickings(self):
        pick_picking = self._create_picking(
            self.warehouse.pick_type_id, self.stock_location, self.output_location
        )
        out_picking = self._create_picking(
            self.warehouse.out_type_id, self.output_location, self.customer_location
        )
        out_move = self._create_move(
            out_picking, self.output_location, self.customer_location
        )
        pick_move = self._create_move(
            pick_picking, self.stock_location, self.output_location
        )
        pick_move.move_dest_ids = [Command.link(out_move.id)]
        batch = self.env["stock.picking.batch"].create(
            {
                "picking_type_id": self.warehouse.pick_type_id.id,
                "picking_ids": [Command.link(pick_picking.id)],
            }
        )

        self.assertEqual(batch.get_out_pickings(), out_picking)
