# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from freezegun import freeze_time

from odoo.tests.common import SavepointCase


class TestStockReportQuantityByLocationByDate(SavepointCase):
    @classmethod
    @freeze_time("2022-02-01")
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.wizard_obj = cls.env["stock.report.quantity.location.date"]

        vals = {
            "name": "Product Test",
            "type": "product",
        }
        cls.product = cls.env["product.product"].create(vals)

        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": cls.product.id,
                "inventory_quantity": 50.0,
                "location_id": cls.stock_location.id,
            }
        )

    def test_wizard(self):
        """
        Create the report with default date (today)
        One line should be present

        Create the report before the stock entry date
        No line should be present
        """
        self.wizard = self.wizard_obj.create(
            {"location_ids": [(4, self.stock_location.id)]}
        )
        self.report = self.wizard.doit()
        wizard_lines = self.env["report.stock.quantity.location.date"].search(
            self.report["domain"]
        )
        lines = wizard_lines.filtered(lambda line: line.product_id == self.product)
        self.assertEqual(1, len(lines))
        self.wizard = self.wizard_obj.create(
            {
                "location_ids": [(4, self.stock_location.id)],
                "pivot_date": "2022-01-01",
            }
        )
        self.report = self.wizard.doit()
        wizard_lines = self.env["report.stock.quantity.location.date"].search(
            self.report["domain"]
        )
        lines = wizard_lines.filtered(lambda line: line.product_id == self.product)
        self.assertEqual(0, len(lines))
