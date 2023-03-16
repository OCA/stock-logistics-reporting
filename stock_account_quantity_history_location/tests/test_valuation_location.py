# Copyright 2020 Tecnativa - David Vidal
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo.addons.stock_quantity_history_location.tests import (
    test_stock_quantity_history_location,
)


class TestValuationLocation(
    test_stock_quantity_history_location.TestStockQuantityHistoryLocation
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sqh_model = cls.env["stock.quantity.history"]
        cls.sqh_model_svl = cls.env["stock.quantity.history"].with_context(
            active_model="stock.valuation.layer"
        )

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

    def test_stock_location_valuation(self):
        wizard = self.sqh_model.create(
            {
                "location_id": self.test_stock_loc.id,
                "include_child_locations": True,
                "inventory_datetime": datetime.today(),
            }
        )
        action = wizard.with_context(company_owned=True).open_at_date()
        qty_svl_prev = self.product.with_context(**action["context"]).quantity_svl
        move = self._create_stock_move(location_dest_id=self.test_stock_loc, qty=60)
        wizard["inventory_datetime"] = move.stock_valuation_layer_ids.create_date
        action = wizard.with_context(company_owned=True).open_at_date()
        product = self.product.with_context(**action["context"])
        self.assertEqual(product.quantity_svl - qty_svl_prev, 60)

    def test_stock_location_valuation_without_location_id(self):
        wizard = self.sqh_model.create(
            {"include_child_locations": True, "inventory_datetime": datetime.today()}
        )
        action = wizard.with_context(company_owned=True, valuation=True).open_at_date()
        qty_svl_prev = self.product.with_context(**action["context"]).quantity_svl
        self._create_stock_move(location_dest_id=self.test_stock_loc, qty=50)
        move = self._create_stock_move(
            location_dest_id=self.child_test_stock_loc, qty=10
        )
        wizard["inventory_datetime"] = move.stock_valuation_layer_ids.create_date
        action = wizard.with_context(company_owned=True).open_at_date()
        product = self.product.with_context(**action["context"])
        self.assertEqual(product.quantity_svl - qty_svl_prev, 60)

    def test_stock_location_valuation_with_svl(self):
        wizard = self.sqh_model_svl.create(
            {
                "location_id": self.test_stock_loc.id,
                "include_child_locations": True,
                "inventory_datetime": datetime.today(),
            }
        )
        action = wizard.with_context(company_owned=True).open_at_date()
        records_prev = self.env[action["res_model"]].search(action["domain"])
        move = self._create_stock_move(location_dest_id=self.test_stock_loc, qty=100)
        wizard["inventory_datetime"] = move.stock_valuation_layer_ids.create_date
        action = wizard.with_context(company_owned=True).open_at_date()
        records = self.env[action["res_model"]].search(action["domain"]) - records_prev
        self.assertEqual(sum(records.mapped("quantity")), 100)

    def test_stock_location_valuation_with_svl_without_location_id(self):
        wizard = self.sqh_model_svl.create(
            {"include_child_locations": True, "inventory_datetime": datetime.today()}
        )
        action = wizard.with_context(company_owned=True).open_at_date()
        records_prev = self.env[action["res_model"]].search(action["domain"])
        self._create_stock_move(location_dest_id=self.test_stock_loc, qty=100)
        move = self._create_stock_move(
            location_dest_id=self.child_test_stock_loc, qty=100
        )
        wizard["inventory_datetime"] = move.stock_valuation_layer_ids.create_date
        action = wizard.with_context(company_owned=True).open_at_date()
        records = self.env[action["res_model"]].search(action["domain"]) - records_prev
        self.assertEqual(sum(records.mapped("quantity")), 200)
