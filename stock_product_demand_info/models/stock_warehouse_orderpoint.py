# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    demand_period_info = fields.Json(
        string="Demand by period",
        compute="_compute_demand_period_info",
        help="Past demand per period. Periods can be configured in General Settings.",
    )

    @api.depends_context("lang")
    def _compute_demand_period_info(self):
        """Compute demand_period_info using orderpoint's warehouse."""
        for orderpoint in self:
            if not orderpoint.product_id:
                orderpoint.demand_period_info = {}
                continue
            values = orderpoint.product_id._get_demand_period_info(
                warehouse=orderpoint.warehouse_id
            )
            orderpoint.demand_period_info = values.get(orderpoint.product_id, {})
