# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from __future__ import annotations

from typing import TYPE_CHECKING

from odoo import api, fields, models
from odoo.tools.misc import formatLang

if TYPE_CHECKING:
    from odoo.addons.stock.models.stock_warehouse import StockWarehouse


class ProductTemplate(models.Model):
    _inherit = "product.template"

    demand_period_info = fields.Json(
        string="Demand by period",
        compute="_compute_demand_period_info",
        help="Past demand per period. Periods can be configured in General Settings.",
    )

    @api.depends_context("lang")
    def _get_demand_period_info(self, warehouse: StockWarehouse | None = None):
        """Sum variants demand_period_info per period."""
        all_variants = self.product_variant_ids
        if not all_variants:  # pragma: no cover
            return {}
        # Prefetch all variants demand period info
        all_variants.fetch(["demand_period_info"])
        res = {}
        # Aggregate periods data
        for template in self:
            res[template] = {}
            for variant in template.product_variant_ids:
                period_info = variant.demand_period_info
                if not period_info:  # pragma: no cover
                    continue
                for period_id, data in period_info.items():
                    if period_id not in res[template]:
                        res[template][period_id] = data.copy()
                    else:
                        res[template][period_id]["value"] += data["value"]
                        res[template][period_id]["formatted_value"] = formatLang(
                            self.env,
                            value=data["value"],
                            dp="Product Unit",
                        )
        return res

    @api.depends_context("lang")
    def _compute_demand_period_info(self):
        """Compute demand_period_info for product (global, no warehouse)."""
        result = self._get_demand_period_info(warehouse=None)
        for template in self:
            template.demand_period_info = result.get(template) or {}
