# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.base.tests.common import BaseCommon


class TestUsageReport(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location_obj = cls.env["stock.location"]
        cls.stock = cls.env.ref("stock.stock_location_stock")
        cls.product_obj = cls.env["product.product"]

        cls.storage_category = cls.env["stock.storage.category"]

        cls.storage_large = cls.storage_category.create(
            {
                "name": "Large Storage",
            }
        )

        cls.storage_medium = cls.storage_category.create(
            {
                "name": "Large Storage",
            }
        )

        cls.product_large_1 = cls.product_obj.create(
            {
                "name": "Product Large 1",
                "type": "product",
            }
        )

        cls.product_large_2 = cls.product_obj.create(
            {
                "name": "Product Large 2",
                "type": "product",
            }
        )

        cls.product_medium_1 = cls.product_obj.create(
            {
                "name": "Product Large 1",
                "type": "product",
            }
        )

        # Create Locations structure
        cls.large_shelves = cls.location_obj.create(
            {
                "name": "Large Shelves",
                "location_id": cls.stock.id,
                "usage": "view",
                "storage_category_id": cls.storage_large.id,
            }
        )

        cls.large_shelf_1 = cls.location_obj.create(
            {
                "name": "Large Shelf 1",
                "location_id": cls.large_shelves.id,
                "usage": "internal",
            }
        )
        cls.large_shelf_2 = cls.location_obj.create(
            {
                "name": "Large Shelf 2",
                "location_id": cls.large_shelves.id,
                "usage": "internal",
            }
        )
        cls.large_shelf_3 = cls.location_obj.create(
            {
                "name": "Large Shelf 3",
                "location_id": cls.large_shelves.id,
                "usage": "internal",
            }
        )

        cls.medium_shelves = cls.location_obj.create(
            {
                "name": "Medium Shelves",
                "location_id": cls.stock.id,
                "usage": "view",
                "storage_category_id": cls.storage_medium.id,
            }
        )

        cls.medium_shelf_1 = cls.location_obj.create(
            {
                "name": "Medium Shelf 1",
                "location_id": cls.medium_shelves.id,
                "usage": "internal",
            }
        )
        cls.medium_shelf_2 = cls.location_obj.create(
            {
                "name": "Medium Shelf 2",
                "location_id": cls.medium_shelves.id,
                "usage": "internal",
            }
        )
        cls.medium_shelf_3 = cls.location_obj.create(
            {
                "name": "Medium Shelf 3",
                "location_id": cls.medium_shelves.id,
                "usage": "internal",
            }
        )

        # Put product large 1 in large shelf 1
        cls._update_quantity(cls.product_large_1, cls.large_shelf_1, 10.0)
        # Put product large 2 in large shelf 3
        cls._update_quantity(cls.product_large_2, cls.large_shelf_3, 10.0)

        # Put product medium 1 in medium shelf 1
        cls._update_quantity(cls.product_medium_1, cls.medium_shelf_1, 10.0)

    @classmethod
    def _update_quantity(cls, product, location, quantity):
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {"product_id": product.id, "location_id": location.id, "quantity": quantity}
        )._apply_inventory()

    def test_usage_report(self):
        self.assertEqual((self.large_shelf_2), self.storage_large.void_location_ids)
        self.assertEqual(1, self.storage_large.void_location_count)
        self.assertAlmostEqual(self.storage_large.occupation_rate, 66.67, places=2)
        self.assertEqual(
            (self.medium_shelf_2 | self.medium_shelf_3),
            self.storage_medium.void_location_ids,
        )
        self.assertEqual(2, self.storage_medium.void_location_count)
        self.storage_medium_void = self.storage_category.create(
            {
                "name": "Medium Storage Void",
            }
        )
        self.medium_shelf_3.storage_category_id = self.storage_medium_void
        self.assertEqual(self.storage_medium_void.occupation_rate, 0.0)
