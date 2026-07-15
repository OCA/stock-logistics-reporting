# Copyright 2019 ForgeFlow S.L.
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields

from .common import TestCommon


class TestStockQuantityHistoryLocation(TestCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")
        cls.main_company = cls.env.ref("base.main_company")
        cls.product = cls.env.ref("product.product_product_3")
        cls.test_stock_loc = cls.env["stock.location"].create(
            {
                "usage": "internal",
                "name": "Test Stock Location",
                "company_id": cls.main_company.id,
            }
        )
        cls.child_test_stock_loc = cls.env["stock.location"].create(
            {
                "usage": "internal",
                "name": "Child Test Stock Location",
                "location_id": cls.test_stock_loc.id,
                "company_id": cls.main_company.id,
            }
        )
        cls._create_stock_move(cls, location_dest_id=cls.child_test_stock_loc, qty=100)

    def get_stock_quantity_history_action(self, location, to_date):
        wizard = self.env["stock.quantity.history"].create(
            {
                "location_id": location.id,
                "inventory_datetime": to_date,
            }
        )
        return wizard.open_at_date()

    def test_stock_quantity_history_location(self):
        current_date = fields.Datetime.now()
        past_date = fields.Datetime.to_datetime("2019-08-10 00:00:00")
        action = self.get_stock_quantity_history_action(
            self.child_test_stock_loc, current_date
        )
        self.assertEqual(action["context"].get("to_date"), current_date)
        self.assertEqual(
            self.product.with_context(**action["context"]).qty_available, 100.0
        )
        action = self.get_stock_quantity_history_action(
            self.child_test_stock_loc, past_date
        )
        to_date_in_context = action["context"].get("to_date")
        self.assertIsNotNone(to_date_in_context)
        self.assertEqual(to_date_in_context, past_date)
        self.assertEqual(
            self.product.with_context(**action["context"]).qty_available, 0.0
        )
        action = self.get_stock_quantity_history_action(
            self.test_stock_loc, current_date
        )
        self.assertEqual(
            self.product.with_context(**action["context"]).qty_available, 100.0
        )
        action = self.get_stock_quantity_history_action(self.test_stock_loc, past_date)
        self.assertEqual(
            self.product.with_context(**action["context"]).qty_available, 0.0
        )
