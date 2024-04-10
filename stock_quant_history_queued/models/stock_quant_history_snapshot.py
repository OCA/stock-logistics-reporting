# Copyright 2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class StockQuantHistorySnapshot(models.Model):
    _inherit = "stock.quant.history.snapshot"
    state = fields.Selection(
        selection_add=[("queued", "In progress"), ("generated",)],
        ondelete={"queued": "set default"},
    )

    def action_generate_stock_quant_history(self):
        self._setup_queue_jobs_generate_stock_quant_history()

    def _setup_queue_jobs_generate_stock_quant_history(self):
        for snapshot in self:
            snapshot.state = "queued"
            snapshot.with_delay(
                priority=snapshot.inventory_date.timestamp()
            )._generate_stock_quant_history()
