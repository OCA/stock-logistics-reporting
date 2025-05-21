# Copyright 2025 Foodles (http://www.foodles.co).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"
    _check_company_auto = True

    stock_history_snapshot_auto_locks_picking = fields.Boolean(
        string="Auto lock picking on snapshot",
        help="When a stock quant history snapshot is generated, "
        "automatically locks all done pickings that are related to the snapshot.",
        default=True,
        groups="stock.group_stock_manager",
    )
