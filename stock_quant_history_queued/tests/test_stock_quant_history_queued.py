from odoo import fields
from odoo.tests import SavepointCase

from odoo.addons.queue_job.tests.common import trap_jobs


class TestStockQuantHistoryQueued(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.stock_history_christmas_2024 = cls.env[
            "stock.quant.history.snapshot"
        ].create(
            {
                "inventory_date": fields.Datetime.from_string("2024-12-25"),
            }
        )
        cls.stock_history_christmas_2023 = cls.env[
            "stock.quant.history.snapshot"
        ].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-12-25"),
            }
        )

    def test_queue_job_setup(self):
        recordset = (
            self.stock_history_christmas_2024 | self.stock_history_christmas_2023
        )
        with trap_jobs() as trap:
            recordset.action_generate_stock_quant_history()

            trap.assert_jobs_count(2)
            trap.assert_enqueued_job(
                self.stock_history_christmas_2023._generate_stock_quant_history,
                properties={"priority": 1703462400},
            )
            trap.assert_enqueued_job(
                self.stock_history_christmas_2024._generate_stock_quant_history,
                properties={"priority": 1735084800},
            )
