# Copyright 2019 ForgeFlow S.L.
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command, fields

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
        cls.group_multi_locations = cls.env.ref("stock.group_stock_multi_locations")

    def test_01_wizard_past_date(self):
        wizard = self.env["stock.quantity.history"].create(
            {
                "location_id": self.test_stock_loc.id,
                "include_child_locations": True,
                "inventory_datetime": fields.Datetime.now(),
            }
        )
        action = wizard.with_context(company_owned=True).open_at_date()
        self.assertEqual(
            self.product.with_context(**action["context"]).qty_available, 100.0
        )
        self.assertEqual(
            self.product.with_context(
                location=self.child_test_stock_loc.id, to_date="2019-08-10"
            ).qty_available,
            0.0,
        )

    def test_02_wizard_current(self):
        wizard = self.env["stock.quantity.history"].create(
            {"location_id": self.test_stock_loc.id, "include_child_locations": False}
        )
        action = wizard.with_context().open_at_date()
        self.assertEqual(action["context"]["compute_child"], False)
        self.assertEqual(action["context"]["location"], self.test_stock_loc.id)
        wizard = self.env["stock.quantity.history"].create(
            {"location_id": self.test_stock_loc.id, "include_child_locations": True}
        )
        action = wizard.with_context().open_at_date()
        self.assertEqual(action["context"]["compute_child"], True)
        self.assertEqual(action["context"]["location"], self.test_stock_loc.id)

    def test_03_get_stock_quant_list_view(self):
        # 1. Get Stock Quant list view without the `group_stock_multi_locations` group
        self.env.user.write(
            {"groups_id": [Command.unlink(self.group_multi_locations.id)]}
        )
        views = [[False, "list"]]
        sq_views = self.env["stock.quant"].get_views(views=views)
        list_view = sq_views.get("views", {}).get("list", {})
        arch = list_view.get("arch", "")
        arch_tree = etree.XML(arch)
        buttons = arch_tree.xpath('//button[@name="action_inventory_at_date"]')
        for button in buttons:
            self.assertEqual(button.get("string"), "Inventory at Date")
        # 2. Now, with the group
        self.env.user.write(
            {"groups_id": [Command.link(self.group_multi_locations.id)]}
        )
        views = [[False, "list"]]
        sq_views = self.env["stock.quant"].get_views(views=views)
        list_view = sq_views.get("views", {}).get("list", {})
        arch = list_view.get("arch", "")
        arch_tree = etree.XML(arch)
        buttons = arch_tree.xpath('//button[@name="action_inventory_at_date"]')
        for button in buttons:
            self.assertEqual(button.get("string"), "Inventory at Date & Location")
