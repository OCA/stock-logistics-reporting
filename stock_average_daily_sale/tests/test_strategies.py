# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo.exceptions import UserError
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

    def test_no_strategy_error(self):
        with self.assertRaises(UserError):
            self.cfg.write(
                {
                    "use_average_daily_strategy": False,
                    "use_average_sales_strategy": False,
                    "use_max_sales_strategy": False,
                }
            )

    def test_individual_strategies(self):
        self.cfg.write(
            {
                "use_average_daily_strategy": True,
                "use_average_sales_strategy": False,
                "use_max_sales_strategy": False,
            }
        )
        self._refresh()
        ads = self.env["stock.average.daily.sale"].search(
            [
                ("location_id", "=", self.location_zone.id),
                ("product_id", "=", self.product.id),
            ]
        )
        self.assertAlmostEqual(
            ads.recommended_qty, ads._get_strategy_qty_average_daily(), places=2
        )

        self.cfg.write(
            {
                "use_average_daily_strategy": False,
                "use_average_sales_strategy": True,
                "use_max_sales_strategy": False,
            }
        )
        self._refresh()
        ads = self.env["stock.average.daily.sale"].search(
            [
                ("location_id", "=", self.location_zone.id),
                ("product_id", "=", self.product.id),
            ]
        )
        ads.invalidate_recordset()
        self.assertAlmostEqual(
            ads.recommended_qty, ads._get_strategy_qty_average_sales(), places=2
        )

        self.cfg.write(
            {
                "use_average_daily_strategy": False,
                "use_average_sales_strategy": False,
                "use_max_sales_strategy": True,
            }
        )
        self._refresh()
        ads = self.env["stock.average.daily.sale"].search(
            [
                ("location_id", "=", self.location_zone.id),
                ("product_id", "=", self.product.id),
            ]
        )
        ads.invalidate_recordset()
        self.assertAlmostEqual(
            ads.recommended_qty, ads._get_strategy_qty_max_sales(), places=2
        )

    def test_multiple_strategies_combined(self):
        self.cfg.write(
            {
                "use_average_daily_strategy": True,
                "use_average_sales_strategy": True,
                "use_max_sales_strategy": True,
            }
        )
        self._refresh()
        ads = self.env["stock.average.daily.sale"].search(
            [
                ("location_id", "=", self.location_zone.id),
                ("product_id", "=", self.product.id),
            ]
        )
        self.assertAlmostEqual(
            ads.recommended_qty,
            max(
                ads._get_strategy_qty_average_daily(),
                ads._get_strategy_qty_average_sales(),
                ads._get_strategy_qty_max_sales(),
            ),
            places=2,
        )
