# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from __future__ import annotations

from typing import TYPE_CHECKING

from odoo import api, fields, models
from odoo.fields import Domain
from odoo.tools.misc import formatLang

if TYPE_CHECKING:
    from typing import Any

    from odoo.orm.types import Self

    from odoo.addons.stock.models.stock_warehouse import StockWarehouse

    from .product_demand_period import ProductDemandPeriod


class ProductProduct(models.Model):
    _inherit = "product.product"

    demand_period_info = fields.Json(
        string="Demand by period",
        compute="_compute_demand_period_info",
        help="Past demand per period. Periods can be configured in General Settings.",
    )

    @api.model
    def _get_demand_period_moves_location_domain(
        self, warehouse: StockWarehouse | None = None
    ) -> Domain:
        """Return the location domain for demand moves.

        Strongly inspired by ``_get_monthly_demand_moves_location_domain`` in
        addons/purchase_stock/models/product.py:
        https://github.com/odoo/odoo/blob/d2ea875acaeb5f29564dddd817caaa957b3a6ba8/addons/purchase_stock/models/product.py#L136-L157

        - With warehouse: moves from that warehouse to customer/production/other wh.
        - Without warehouse (product form): all outgoing to customer or production.
        """
        if warehouse:
            return Domain.AND(
                [
                    Domain("location_id.warehouse_id", "=", warehouse.id),
                    Domain.OR(
                        [
                            Domain("location_dest_id.warehouse_id", "!=", warehouse.id),
                            Domain(
                                "location_final_id.warehouse_id", "!=", warehouse.id
                            ),
                        ]
                    ),
                    Domain("location_dest_id.usage", "!=", "inventory"),
                ]
            )
        # No warehouse: all outgoing to customer or production (exclude inventory)
        return Domain.AND(
            [
                Domain.OR(
                    [
                        Domain(
                            "location_dest_id.usage", "in", ["customer", "production"]
                        ),
                        Domain(
                            "location_final_id.usage", "in", ["customer", "production"]
                        ),
                    ]
                ),
                Domain("location_dest_id.usage", "!=", "inventory"),
            ]
        )

    @api.model
    def _get_demand_period_moves_domain(
        self,
        warehouse: StockWarehouse | None,
        period: ProductDemandPeriod,
        product_ids: list[int],
    ) -> Domain:
        """Return the full domain for demand moves in the given period."""
        moves_states = ["assigned", "confirmed", "partially_available", "done"]
        base_domain = Domain(
            [
                ("company_id", "=", self.env.company.id),
                ("product_id", "in", product_ids),
                ("date", ">=", period.start_expression),
                ("date", "<=", period.end_expression),
                ("state", "in", moves_states),
                ("product_qty", ">", 0),
            ]
        )
        return Domain.AND(
            [base_domain, self._get_demand_period_moves_location_domain(warehouse)]
        )

    def _get_demand_period_info(
        self, warehouse: StockWarehouse | None = None
    ) -> dict[Self, dict[int, dict[str, Any]]]:
        """Return demand_period_info dict per product id (batch, one query per period).

        Returns {product: {period_id: {sequence, name, value}, ...}, ...}.
        Used by _compute_demand_period_info and by stock.warehouse.orderpoint.
        """
        if not self:  # pragma: no cover
            return {}
        periods = self.env["product.demand.period"].search([("active", "=", True)])
        if not periods:  # pragma: no cover
            return {}
        result = {}
        for period in periods:
            groups = self.env["stock.move"]._read_group(
                self._get_demand_period_moves_domain(warehouse, period, self.ids),
                groupby=["product_id"],
                aggregates=["product_qty:sum"],
            )
            period_qty_by_product = dict(groups)
            period_data = period.read(period._get_demand_period_info_fnames())[0]
            for product in self:
                value = period_qty_by_product.get(product, 0.0)
                result.setdefault(product, {})[period.id] = dict(
                    dict(
                        period_data,
                        value=value,
                        formatted_value=formatLang(
                            self.env, value=value, dp="Product Unit"
                        ),
                    )
                )
        return result

    @api.depends_context("lang")
    def _compute_demand_period_info(self):
        """Compute demand_period_info for product (global, no warehouse)."""
        result = self._get_demand_period_info(warehouse=None)
        for product in self:
            product.demand_period_info = result.get(product) or {}
