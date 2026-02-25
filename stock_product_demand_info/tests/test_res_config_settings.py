# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestResConfigSettings(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.period_7d = cls.env.ref("stock_product_demand_info.period_last_7_days")
        cls.period_last_month = cls.env.ref(
            "stock_product_demand_info.period_last_month"
        )
        cls.period_last_30_days = cls.env.ref(
            "stock_product_demand_info.period_last_30_days"
        )
        # Archive all periods expect 7d
        cls.env["product.demand.period"].search([]).active = False
        cls.period_7d.active = True

    def test_compute_demand_period_ids(self):
        settings = self.env["res.config.settings"].create({})
        self.assertEqual(settings.demand_period_ids, self.period_7d)
        # Now activate the last month period
        self.period_last_month.active = True
        settings.invalidate_recordset(["demand_period_ids"])
        self.assertEqual(
            settings.demand_period_ids, self.period_7d | self.period_last_month
        )
        # Now archive 7d period
        self.period_7d.active = False
        settings.invalidate_recordset(["demand_period_ids"])
        self.assertEqual(settings.demand_period_ids, self.period_last_month)

    def test_inverse_demand_period_ids(self):
        settings = self.env["res.config.settings"].create({})
        # Activate the last month period from settings
        settings.demand_period_ids = self.period_7d | self.period_last_month
        self.assertEqual(
            self.env["product.demand.period"].search([("active", "=", True)]),
            self.period_7d | self.period_last_month,
        )
        # Deactivate the 7d period from settings
        settings.demand_period_ids -= self.period_7d
        self.assertEqual(
            self.env["product.demand.period"].search([("active", "=", True)]),
            self.period_last_month,
        )
