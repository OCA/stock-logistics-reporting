# Copyright 2025 Foodles (http://www.foodles.co).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    stock_history_snapshot_auto_locks_picking = fields.Boolean(
        related="company_id.stock_history_snapshot_auto_locks_picking",
        readonly=False,
        groups="stock.group_stock_manager",
    )
