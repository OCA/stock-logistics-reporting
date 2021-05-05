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

    def test_wizard_past_date(self):
        wizard = self.env["stock.quantity.history"].create(
            {
                "location_id": self.test_stock_loc.id,
                "include_child_locations": True,
                "inventory_datetime": fields.Datetime.now(),
            }
        )
        action = wizard.with_context(company_owned=True).open_at_date()
        self.assertEquals(
            self.product.with_context(action["context"]).qty_available, 100.0
        )
        self.assertEquals(
            self.product.with_context(
                location=self.child_test_stock_loc.id, to_date="2019-08-10"
            ).qty_available,
            0.0,
        )

    def test_wizard_current(self):
        wizard = self.env["stock.quantity.history"].create(
            {"location_id": self.test_stock_loc.id, "include_child_locations": False}
        )
        action = wizard.with_context().open_at_date()
        self.assertEquals(action["context"]["compute_child"], False)
        self.assertEquals(action["context"]["location"], self.test_stock_loc.id)
        wizard = self.env["stock.quantity.history"].create(
            {"location_id": self.test_stock_loc.id, "include_child_locations": True}
        )
        action = wizard.with_context().open_at_date()
        self.assertEquals(action["context"]["compute_child"], True)
        self.assertEquals(action["context"]["location"], self.test_stock_loc.id)
