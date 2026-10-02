# Copyright 2026 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.orm.models import parse_read_group_spec
from odoo.tools import SQL

# Computed fields whose sum is computed in Python when grouping
STOCK_SUM_FIELDS = (
    "qty_available",
    "free_qty",
    "incoming_qty",
    "outgoing_qty",
    "virtual_available",
    "total_value",
)
IDS_AGGREGATE = "id:array_agg"
CURRENCY_AGGREGATE = "company_currency_id:array_agg_distinct"


class ProductProduct(models.Model):
    _inherit = "product.product"

    # Setting an aggregator makes the web client request these aggregates
    qty_available = fields.Float(aggregator="sum")
    free_qty = fields.Float(aggregator="sum")
    incoming_qty = fields.Float(aggregator="sum")
    outgoing_qty = fields.Float(aggregator="sum")
    virtual_available = fields.Float(aggregator="sum")
    total_value = fields.Monetary(aggregator="sum")

    def _is_stock_sum_aggregate(self, aggregate_spec):
        if aggregate_spec == CURRENCY_AGGREGATE:
            return True
        if aggregate_spec == "__count":
            return False
        fname, property_name, func = parse_read_group_spec(aggregate_spec)
        return (
            not property_name
            and fname in STOCK_SUM_FIELDS
            and func in ("sum", "sum_currency")
        )

    def _read_group_select(self, aggregate_spec, query):
        # These fields aren't stored, so they can't be aggregated in SQL. The
        # real values are computed in `_read_group`, but we need a valid SQL
        # expression to make the ORM consider these aggregates as valid.
        if self._is_stock_sum_aggregate(aggregate_spec):
            return SQL("NULL")
        return super()._read_group_select(aggregate_spec, query)

    def _read_group(
        self,
        domain,
        groupby=(),
        aggregates=(),
        having=(),
        offset=0,
        limit=None,
        order=None,
    ):
        stock_aggregates = [
            spec for spec in aggregates if self._is_stock_sum_aggregate(spec)
        ]
        if not stock_aggregates:
            return super()._read_group(
                domain,
                groupby=groupby,
                aggregates=aggregates,
                having=having,
                offset=offset,
                limit=limit,
                order=order,
            )
        # Replace the stock aggregates by the ids of the records of each group
        other_aggregates = [spec for spec in aggregates if spec not in stock_aggregates]
        rows = super()._read_group(
            domain,
            groupby=groupby,
            aggregates=[*other_aggregates, IDS_AGGREGATE],
            having=having,
            offset=offset,
            limit=limit,
            order=order,
        )
        nb_groupby = len(groupby)
        group_ids = [set(filter(None, row[-1] or [])) for row in rows]
        products = self.browse(set().union(*group_ids))
        values_by_field = {}
        for fname in {
            parse_read_group_spec(spec)[0]
            for spec in stock_aggregates
            if spec != CURRENCY_AGGREGATE
        }:
            # Batch compute the fields for all the products of all groups
            values_by_field[fname] = dict(
                zip(products.ids, products.mapped(fname), strict=False)
            )
        currency_ids = [self.env.company.currency_id.id]
        result = []
        for row, ids in zip(rows, group_ids, strict=False):
            groupby_values = row[:nb_groupby]
            other_values = iter(row[nb_groupby:-1])
            aggregate_values = []
            for spec in aggregates:
                if spec == CURRENCY_AGGREGATE:
                    aggregate_values.append(currency_ids)
                elif spec in stock_aggregates:
                    values = values_by_field[parse_read_group_spec(spec)[0]]
                    aggregate_values.append(sum(values[id_] for id_ in ids))
                else:
                    aggregate_values.append(next(other_values))
            result.append((*groupby_values, *aggregate_values))
        return result
