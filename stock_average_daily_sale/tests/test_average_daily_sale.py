# Copyright 2022 ACSONE SA/NV
# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from statistics import stdev

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo.fields import Datetime

from .common import CommonAverageSaleTest


class TestAverageDailySale(CommonAverageSaleTest):
    """Test materialized view"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        move_1_date = Datetime.to_string(cls.now - relativedelta(days=6))
        with freeze_time(move_1_date):
            cls._make_move(cls.product, cls.location_bin, 10.0)
            cls._make_move(cls.product, cls.location_bin, 5.0)
        move_2_date = Datetime.to_string(cls.now - relativedelta(days=4))
        with freeze_time(move_2_date):
            cls._make_move(cls.product, cls.location_bin, 12.0)

    def test_query_ok(self):
        """Test normal case"""
        self.env.flush_all()
        self._refresh()
        avg_product = self.env["stock.average.daily.sale"].search(
            [
                ("location_id", "=", self.location_zone.id),
                ("product_id", "=", self.product.id),
            ]
        )
        self.assertRecordValues(
            avg_product,
            [
                {
                    "warehouse_id": self.warehouse_0.id,
                    "location_id": self.location_zone.id,
                    "abc_classification_level": self.product.abc_storage,
                    "average_qty_by_sale": (10 + 5 + 12) / 3,
                    "average_daily_sales_count": 3 / 7,
                    "max_daily_qty": 15,
                    "average_daily_qty": (10 + 5 + 12) / 7,
                    "nbr_sales": 3.0,
                    "daily_standard_deviation": stdev([15, 12, 0, 0, 0, 0, 0]),
                }
            ],
        )

    def test_query_other_product_excluded(self):
        """Test other product move has no impact"""
        product_2 = self.env["product.product"].create(
            {
                "name": "Product 2",
                "type": "product",
            }
        )
        inventory_date = Datetime.to_string(self.now - relativedelta(self.now, days=5))
        with freeze_time(inventory_date):
            self.inventory_obj.create(
                {
                    "product_id": product_2.id,
                    "inventory_quantity": 50.0,
                    "location_id": self.location_bin.id,
                }
            )._apply_inventory()
        move_date = Datetime.to_string(self.now - relativedelta(days=4))
        with freeze_time(move_date):
            self._make_move(product_2, self.location_bin, 12.0)
        self.test_query_ok()

    def test_query_other_zone_excluded(self):
        """Test other zone move has no impact"""
        location_zone_2 = self.location_obj.create(
            {
                "name": "Zone Location",
                "location_id": self.warehouse_0.lot_stock_id.id,
            }
        )
        self.cfg.copy({"location_id": location_zone_2.id})
        location_bin_2 = self.location_obj.create(
            {"name": "Bin Location 2", "location_id": location_zone_2.id}
        )
        inventory_date = Datetime.to_string(self.now - relativedelta(self.now, days=5))
        with freeze_time(inventory_date):
            self.inventory_obj.create(
                {
                    "product_id": self.product.id,
                    "inventory_quantity": 50.0,
                    "location_id": location_bin_2.id,
                }
            )._apply_inventory()
        move_date = Datetime.to_string(self.now - relativedelta(days=4))
        with freeze_time(move_date):
            self._make_move(self.product, location_bin_2, 8)
        self.test_query_ok()

    def test_query_reception_excluded(self):
        """Test reception has no impact"""
        move_date = Datetime.to_string(self.now - relativedelta(days=4))
        with freeze_time(move_date):
            move = self.move_obj.create(
                {
                    "product_id": self.product.id,
                    "name": self.product.name,
                    "location_id": self.customers.id,
                    "location_dest_id": self.location_bin.id,
                    "product_uom_qty": 20,
                }
            )
            move._action_confirm()
            move._action_assign()
            move.quantity_done = move.product_uom_qty
            move._action_done()
        self.test_query_ok()

    def test_query_inventory_excluded(self):
        """Test inventory has no impact"""
        move_date = Datetime.to_string(self.now - relativedelta(days=4))
        with freeze_time(move_date):
            self.inventory_obj.create(
                {
                    "product_id": self.product.id,
                    "inventory_quantity": 100.0,
                    "location_id": self.location_bin.id,
                }
            )._apply_inventory()
        move_date = Datetime.to_string(self.now - relativedelta(days=2))
        with freeze_time(move_date):
            self.inventory_obj.create(
                {
                    "product_id": self.product.id,
                    "inventory_quantity": 1.0,
                    "location_id": self.location_bin.id,
                }
            )._apply_inventory()
        self.test_query_ok()

    def test_query_horizon(self):
        """Test moves on today and period-1d have no impact"""
        move_1_date = Datetime.to_string(self.now)
        with freeze_time(move_1_date):
            self._make_move(self.product, self.location_bin, 5.0)
        move_2_date = Datetime.to_string(self.now - relativedelta(days=8))
        with freeze_time(move_2_date):
            self._make_move(self.product, self.location_bin, 7.0)
        self.test_query_ok()

    def test_view_refreshed(self):
        self._refresh()
        with self.assertNoLogs(
            "odoo.addons.stock_average_daily_sale.models.stock_average_daily_sale",
            level="DEBUG",
        ):
            self.env["stock.average.daily.sale"].search_read(
                [("product_id", "=", self.product.id)]
            )
