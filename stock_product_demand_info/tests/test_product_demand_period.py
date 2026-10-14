# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta
from unittest import mock

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError
from odoo.fields import Command

from odoo.addons.stock_product_demand_info.models.product_demand_period import (
    parse_date,
    parse_iso_date,
)

from .common import StockProductDemandInfoCommon


class TestProductDemandPeriod(StockProductDemandInfoCommon):
    def test_parse_iso_date_datetime_zulu(self):
        value = parse_iso_date("2026-05-28T12:30:45Z")
        self.assertIsInstance(value, datetime)
        self.assertIsNotNone(value.tzinfo)

    def test_parse_iso_date_invalid(self):
        with self.assertRaisesRegex(ValueError, "Invalid term"):
            parse_iso_date("2026-99-99")

    def test_parse_date_empty(self):
        with self.assertRaisesRegex(ValueError, "Empty date value"):
            parse_date("   ", self.env)

    def test_parse_date_invalid_term_operator(self):
        with self.assertRaisesRegex(ValueError, "Invalid term"):
            parse_date("today *2d", self.env)

    @freeze_time("2026-05-27 16:45:00")
    def test_parse_date_weekday_and_week_start(self):
        next_monday = parse_date("today +monday", self.env)
        previous_monday = parse_date("today -monday", self.env)
        week_start = parse_date("today +week_start", self.env)

        self.assertIsInstance(next_monday, date)
        self.assertIsInstance(previous_monday, date)
        self.assertIsInstance(week_start, date)
        self.assertLessEqual(previous_monday, next_monday)

    @freeze_time("2026-05-27 16:45:00")
    def test_parse_date_equal_weekday_truncates_datetime(self):
        value = parse_date("now =monday", self.env, naive=False)
        self.assertIsInstance(value, datetime)
        self.assertEqual(value.hour, 0)
        self.assertEqual(value.minute, 0)
        self.assertEqual(value.second, 0)

    def test_parse_date_equal_week_not_supported(self):
        with self.assertRaisesRegex(ValueError, "Invalid term"):
            parse_date("now =1w", self.env)

    @freeze_time("2026-05-27 16:45:00")
    def test_parse_date_naive_timezone_conversion(self):
        aware = parse_date("now", self.env, naive=False)
        naive = parse_date("now", self.env, naive=True)
        self.assertIsInstance(aware, datetime)
        self.assertIsNotNone(aware.tzinfo)
        self.assertIsInstance(naive, datetime)
        self.assertIsNone(naive.tzinfo)

    def test_validation_invalid_expression_create(self):
        with self.assertRaisesRegex(UserError, "Invalid date expression"):
            self.env["product.demand.period"].create(
                {
                    "name": "Bad",
                    "start_expression": "invalid-expression",
                    "end_expression": "today",
                }
            )

    def test_validation_invalid_expression_write(self):
        period = self.env["product.demand.period"].create(
            {
                "name": "Good",
                "start_expression": "today -7d",
                "end_expression": "today",
            }
        )
        with self.assertRaisesRegex(UserError, "Invalid date expression"):
            period.write({"start_expression": "bad"})

    def test_validation_start_after_end(self):
        with self.assertRaisesRegex(
            UserError, "Start expression must be before or equal to end"
        ):
            self.env["product.demand.period"].create(
                {
                    "name": "Reversed",
                    "start_expression": "today",
                    "end_expression": "today -7d",
                }
            )

    def test_demand_product_no_warehouse(self):
        """Product demand_period_info aggregates outgoing moves when no warehouse."""
        self.period_7d.active = True
        self._create_outgoing_move(self.product, self.today - timedelta(days=3), 10.0)
        self._create_outgoing_move(self.product, self.today - timedelta(days=1), 5.0)
        self.product.invalidate_recordset(["demand_period_info"])
        key = str(self.period_7d.id)
        self.assertTrue(self.product.demand_period_info)
        self.assertIn(key, self.product.demand_period_info)
        self.assertEqual(self.product.demand_period_info[key]["value"], 15.0)
        self.assertEqual(self.product.demand_period_info[key]["name"], "Last 7 days")
        self.assertIn("sequence", self.product.demand_period_info[key])

    def test_demand_orderpoint_warehouse(self):
        """Orderpoint demand_period_info is warehouse-scoped."""
        self.period_7d.active = True
        self._create_outgoing_move(self.product, self.today - timedelta(days=2), 7.0)
        self.orderpoint.invalidate_recordset(["demand_period_info"])
        key = str(self.period_7d.id)
        self.assertTrue(self.orderpoint.demand_period_info)
        self.assertIn(key, self.orderpoint.demand_period_info)
        self.assertEqual(self.orderpoint.demand_period_info[key]["value"], 7.0)
        self.assertEqual(self.orderpoint.demand_period_info[key]["name"], "Last 7 days")

    def test_orderpoint_without_product(self):
        orderpoint = self.env["stock.warehouse.orderpoint"].new(
            {
                "warehouse_id": self.warehouse.id,
            }
        )
        orderpoint._compute_demand_period_info()
        self.assertFalse(orderpoint.demand_period_info)

    def test_orderpoint_missing_product_key_in_values(self):
        self.period_7d.active = True
        with mock.patch.object(
            type(self.product),
            "_get_demand_period_info",
            return_value={},
        ):
            self.orderpoint.invalidate_recordset(["demand_period_info"])
            self.assertFalse(self.orderpoint.demand_period_info)

    @freeze_time("2026-05-28 12:00:00")
    def test_ytd_excludes_today(self):
        """Test YTD demand excludes outgoing moves dated today."""
        today = fields.Date.today()
        self.period_ytd.active = True
        self._create_outgoing_move(self.product, today - timedelta(days=1), 2000.0)
        self._create_outgoing_move(self.product, today, 800.0)
        self.product.invalidate_recordset(["demand_period_info"])
        key = str(self.period_ytd.id)
        self.assertEqual(self.product.demand_period_info[key]["value"], 2000.0)

    @freeze_time("2026-05-28 12:00:00")
    def test_orderpoint_ytd_excludes_today(self):
        """Test orderpoint YTD demand excludes outgoing moves dated today."""
        today = fields.Date.today()
        self.period_ytd.active = True
        self._create_outgoing_move(self.product, today - timedelta(days=1), 2000.0)
        self._create_outgoing_move(self.product, today, 800.0)
        self.orderpoint.invalidate_recordset(["demand_period_info"])
        key = str(self.period_ytd.id)
        self.assertEqual(self.orderpoint.demand_period_info[key]["value"], 2000.0)

    def test_demand_no_active_periods(self):
        """With no active periods, demand_period_info is empty."""
        self.product.invalidate_recordset(["demand_period_info"])
        self.assertFalse(self.product.demand_period_info)

    def test_demand_period_no_moves_in_range(self):
        """Period with no moves in range yields zero for that period."""
        self.period_7d.active = True
        self.product.invalidate_recordset(["demand_period_info"])
        key = str(self.period_7d.id)
        self.assertTrue(self.product.demand_period_info)
        self.assertIn(key, self.product.demand_period_info)
        self.assertEqual(self.product.demand_period_info[key]["value"], 0.0)
        self.assertEqual(self.product.demand_period_info[key]["name"], "Last 7 days")

    def test_demand_template_sum_of_variants(self):
        """product.template demand_period_info is the sum of its variants' demand."""
        self.period_7d.active = True
        # Product template with two variants
        attr_size = self.env["product.attribute"].create({"name": "Size"})
        attr_values = self.env["product.attribute.value"].create(
            [
                {"name": "S", "attribute_id": attr_size.id},
                {"name": "M", "attribute_id": attr_size.id},
                {"name": "L", "attribute_id": attr_size.id},
            ]
        )
        template = self.env["product.template"].create(
            {
                "name": "Product With Variants",
                "detailed_type": "product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": attr_size.id,
                            "value_ids": [Command.set(attr_values.ids)],
                        }
                    )
                ],
            }
        )
        # Create outgoing moves for the variants
        # (variant_l has no moves)
        variant_s, variant_m, variant_l = template.product_variant_ids
        self._create_outgoing_move(variant_s, self.today - timedelta(days=2), 10.0)
        self._create_outgoing_move(variant_m, self.today - timedelta(days=1), 5.0)
        template.invalidate_recordset(["demand_period_info"])
        template.product_variant_ids.invalidate_recordset(["demand_period_info"])
        # Check the computed values
        key = str(self.period_7d.id)
        self.assertEqual(variant_s.demand_period_info[key]["value"], 10.0)
        self.assertEqual(variant_m.demand_period_info[key]["value"], 5.0)
        self.assertEqual(variant_l.demand_period_info[key]["value"], 0.0)
        self.assertIn(key, template.demand_period_info)
        self.assertEqual(template.demand_period_info[key]["value"], 15.0)
        self.assertEqual(template.demand_period_info[key]["name"], "Last 7 days")

    def test_demand_two_periods_enabled(self):
        """With two active periods, demand is computed per period (e.g. 7d vs 30d)."""
        self.period_7d.active = True
        self.period_last_30_days.active = True
        self._create_outgoing_move(self.product, self.today - timedelta(days=5), 10.0)
        self._create_outgoing_move(self.product, self.today - timedelta(days=20), 5.0)
        self.product.invalidate_recordset(["demand_period_info"])
        key_7d = str(self.period_7d.id)
        key_30d = str(self.period_last_30_days.id)
        self.assertIn(key_7d, self.product.demand_period_info)
        self.assertIn(key_30d, self.product.demand_period_info)
        self.assertEqual(self.product.demand_period_info[key_7d]["value"], 10.0)
        self.assertEqual(self.product.demand_period_info[key_30d]["value"], 15.0)
        self.assertEqual(self.product.demand_period_info[key_7d]["name"], "Last 7 days")
        self.assertEqual(
            self.product.demand_period_info[key_30d]["name"], "Last 30 days"
        )
