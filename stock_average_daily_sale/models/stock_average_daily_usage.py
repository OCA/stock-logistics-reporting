# Copyright 2018 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2021 ACSONE SA/NV
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import closing
from math import sqrt

from psycopg2.errors import ObjectNotInPrerequisiteState
from psycopg2.extensions import AsIs

from odoo import _, api, fields, models, registry
from odoo.tools import config

from odoo.addons.stock_storage_type_putaway_abc.models.stock_location import (
    ABC_SELECTION,
)

_logger = logging.getLogger(__name__)


class StockAverageDailyUsage(models.Model):
    _name = "stock.average.daily.usage"
    _auto = False
    _order = "abc_classification_level ASC, product_id ASC"
    _description = "Average Daily Consumption for Products"

    abc_classification_level = fields.Selection(
        selection=ABC_SELECTION, string="ABC", required=True, readonly=True, index=True
    )
    average_daily_consumption_count = fields.Float(
        required=True,
        digits="Product Unit of Measure",
        help="Average number of consumption operations per day for this product over "
        "the period.",
    )
    average_qty_by_consumption = fields.Float(
        string="Average Qty by Consumption",
        required=True,
        digits="Product Unit of Measure",
        help="Quantity delivered on average per consumption operation for this "
        "product over the period.",
    )
    average_daily_qty = fields.Float(
        digits="Product Unit of Measure",
        required=True,
        help="Average quantity consumed per day for this product over the period.",
    )
    max_daily_qty = fields.Float(
        digits="Product Unit of Measure",
        required=True,
        help="Maximum quantity consumed in a single day for this product over the "
        "period.",
    )
    config_id = fields.Many2one(
        string="Stock Average Daily Usage Configuration",
        comodel_name="stock.average.daily.usage.config",
        required=True,
    )
    date_from = fields.Date(string="From", required=True)
    date_to = fields.Date(string="To", required=True)
    is_mto = fields.Boolean(
        string="On Order",
        readonly=True,
        store=True,
        index=True,
    )
    nbr_consumptions = fields.Integer(
        string="Number of Consumptions",
        required=True,
        help="Total number of consumption moves for this product over the "
        "complete period.",
    )
    product_id = fields.Many2one(
        comodel_name="product.product", string="Product", required=True, index=True
    )
    safety = fields.Float(
        required=True,
        compute="_compute_safety",
        help="Safety stock to cover the variability of the quantity consumed "
        "each day. Formula: daily standard deviation * safety factor * "
        "sqrt(number of days in the period)",
    )

    def _compute_safety(self):
        for rec in self:
            lt = rec.config_id.number_days_qty_in_stock
            rec.safety = (
                rec.daily_standard_deviation * rec.config_id.safety_factor * sqrt(lt)
            )

    recommended_qty = fields.Float(
        required=True,
        compute="_compute_recommended_qty",
        digits="Product Unit of Measure",
        help="Minimal recommended quantity in stock. Equal to the max "
        "recommended quantity across all active strategies.",
    )

    def _get_strategy_qty_average_daily(self):
        if not self.config_id.use_average_daily_strategy:
            return 0.0
        return (
            self.config_id.number_days_qty_in_stock * self.average_daily_qty
        ) + self.safety

    def _get_strategy_qty_average_consumption(self):
        if not self.config_id.use_average_consumption_strategy:
            return 0.0
        return (
            self.config_id.average_consumption_factor * self.average_qty_by_consumption
        )

    def _get_strategy_qty_max_consumption(self):
        if not self.config_id.use_max_consumption_strategy:
            return 0.0
        return self.max_daily_qty * self.config_id.max_consumption_factor

    @api.model
    def _get_strategy_methods_names(self):
        """Collect all strategy calculation method names matching prefix
        `_get_strategy_qty_`."""
        return [
            attr_name
            for attr_name in dir(self)
            if attr_name.startswith("_get_strategy_qty_")
            and callable(getattr(self, attr_name))
        ]

    def _compute_recommended_qty(self):
        method_names = self._get_strategy_methods_names()
        for rec in self:
            strategy_qtys = [
                getattr(rec, method_name)() for method_name in method_names
            ]
            rec.recommended_qty = max(strategy_qtys, default=0.0)

    sale_ok = fields.Boolean(
        string="Can be Sold",
        readonly=True,
        index=True,
        help="Specify if the product can be selected in a sales order line.",
    )
    daily_standard_deviation = fields.Float(
        string="Daily Qty Standard Deviation", required=True
    )
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", required=True)
    location_id = fields.Many2one(comodel_name="stock.location", required=True)

    @classmethod
    def _check_materialize_view_populated(cls, cr):
        """
        Check if the materialized view is populated

        :param cr: database cursor
        :return: True if the materialized view is populated, False otherwise
        """
        cr.execute(
            "SELECT ispopulated FROM pg_matviews WHERE matviewname = %s;",
            (cls._table,),
        )
        records = cr.fetchone()
        return records and records[0]

    @api.model
    def _check_view(self):
        cr = registry(self._cr.dbname).cursor()
        with closing(cr):
            try:
                return self._check_materialize_view_populated(cr)
            except ObjectNotInPrerequisiteState:
                _logger.warning(
                    _("The materialized view has not been populated. Launch the cron.")
                )
                return False
            except Exception as e:
                raise e

    # pylint: disable=redefined-outer-name
    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        if not config["test_enable"] and not self._check_view():
            return self.browse()
        return super().search(
            domain=domain, offset=offset, limit=limit, order=order, count=count
        )

    @api.model
    def get_refresh_date(self):
        return self.env["ir.config_parameter"].get_param(
            "stock_average_daily_usage_refresh_date"
        )

    @api.model
    def set_refresh_date(self, date=None):
        if date is None:
            date = fields.Datetime.now()
        self.env["ir.config_parameter"].set_param(
            "stock_average_daily_usage_refresh_date", date
        )

    @api.model
    def refresh_view(self):
        concurrently = ""
        if self._check_materialize_view_populated(self.env.cr):
            concurrently = "CONCURRENTLY"
        self.env.cr.execute(
            "refresh materialized view %s %s",
            (
                AsIs(concurrently),
                AsIs(self._table),
            ),
        )
        self.set_refresh_date()

    def _create_materialized_view(self):
        self.env.cr.execute(
            "DROP MATERIALIZED VIEW IF EXISTS %s CASCADE", (AsIs(self._table),)
        )
        now = fields.Datetime.now()
        self.env.cr.execute(
            """ -- # noqa: B950
            CREATE MATERIALIZED VIEW %(table)s AS (
                -- Create a consolidated definition of parameters used into the average daily
                -- consumption computation. Parameters are specified by product ABC class
                WITH cfg AS (
                    SELECT
                        stock_average_daily_usage_config.*,
                        dts.date_from,
                        dts.date_to,
                        sl.parent_path AS location_parent_path,
                        -- the number of days between start and end computed by
                        -- removing Saturday and Sunday if weekends should be excluded
                        (SELECT count(d::date)
                            FROM generate_series (date_from, date_to, '1 day') AS gs(d)
                            WHERE NOT exclude_weekends OR EXTRACT(ISODOW FROM d) NOT IN (6,7)
                        ) AS total_days
                    FROM
                        stock_average_daily_usage_config
                    JOIN stock_location sl ON stock_average_daily_usage_config.location_id = sl.id
                    JOIN LATERAL (
                        SELECT
                        -- start of the analyzed period computed from the original cfg
                        (%(now)s::date - (period_value::text || ' ' || period_name::text)::interval)::date AS date_from,
                        -- end of the analyzed period; don't consider today as we don't have all figures yet
                        (%(now)s::date - '1 day'::interval)::date AS date_to
                    ) dts ON true
                    WHERE
                        stock_average_daily_usage_config.active = True
                ),
                -- Collect max and min date on all moves to avoid collecting moves outside observed scopes
                cfg_bounds AS (
                    SELECT
                        min(date_from) AS min_date,
                        max(date_to) AS max_date
                    FROM cfg
                ),
                -- Collect products
                cfg_products AS (
                    SELECT
                        cfg.id AS config_id,
                        pp.id AS product_id
                    FROM
                        cfg
                    JOIN product_template pt
                        ON cfg.abc_classification_level = COALESCE(pt.abc_storage, 'c')
                    JOIN product_product pp
                        ON pt.id = pp.product_tmpl_id
                ),
                -- Collect config locations
                cfg_locations AS (
                    SELECT
                        cfg.id AS config_id,
                        sl.id AS location_id
                    FROM
                        cfg
                    JOIN
                        stock_location sl
                        ON sl.parent_path LIKE cfg.location_parent_path || '%%'
                ),
                -- Prefilter moves used to compute consumption to avoid processing all moves of the system.
                -- Only moves with a date between min and max bounds of configs are kept
                filtered_moves AS (
                    SELECT
                        sm.id,
                        sm.product_id,
                        sm.location_id,
                        sm.location_dest_id,
                        sm.product_uom_qty,
                        sm.date,
                        sm.date::date AS day
                    FROM
                        stock_move sm
                    CROSS JOIN
                        cfg_bounds cb
                    WHERE
                        sm.state = 'done'
                        AND sm.product_uom_qty > 0
                        AND sm.date >= cb.min_date
                        AND sm.date < cb.max_date + interval '1 day'
                        AND EXISTS (SELECT 1 FROM cfg_products cp WHERE cp.product_id = sm.product_id)
                ),
                -- Collect moves from config location hierarchy to outside that hierarchy
                consumption AS (
                    SELECT
                        fm.product_id,
                        fm.product_uom_qty,
                        cfg.id AS config_id,
                        fm.day
                    FROM
                        filtered_moves fm
                    JOIN stock_location sl_dest
                        ON sl_dest.id = fm.location_dest_id
                        AND sl_dest.usage != 'inventory'
                    JOIN cfg_products cp
                        ON cp.product_id = fm.product_id
                    JOIN cfg
                        ON cfg.id = cp.config_id
                    JOIN stock_location sl_src
                        ON sl_src.id = fm.location_id
                    WHERE
                        fm.date >= cfg.date_from
                        AND fm.date < cfg.date_to + interval '1 day'
                        -- source inside hierarchy
                        AND sl_src.parent_path LIKE cfg.location_parent_path || '%%'
                        -- destination outside hierarchy
                        AND sl_dest.parent_path NOT LIKE cfg.location_parent_path || '%%'
                ),
                -- Aggregate on a daily basis
                daily_consumption AS (
                    SELECT
                        config_id,
                        day,
                        product_id,
                        SUM(product_uom_qty) AS qty,
                        COUNT(product_uom_qty) AS count
                    FROM consumption
                    GROUP BY config_id, day, product_id
                ),
                -- Compute average and max metrics
                average_max AS(
                    SELECT
                        dc.product_id,
                        dc.config_id,
                        MAX(dc.qty) AS daily_max_qty,
                        SUM(dc.qty) / cfg.total_days AS daily_average_qty,
                        SUM(dc.qty) / SUM(dc.count) AS average_qty_by_consumption,
                        SUM(dc.count) AS total_amount,
                        SUM(dc.count) / cfg.total_days AS average_amount,
                        cfg.total_days,
                        count(*) AS count_days,
                        array_agg(dc.qty)
                            FILTER (WHERE NOT cfg.exclude_weekends OR EXTRACT(ISODOW FROM dc.day) NOT IN (6,7))
                            AS daily_consumption_arr
                    FROM daily_consumption dc
                    LEFT JOIN cfg ON cfg.id = dc.config_id
                    GROUP BY dc.product_id, dc.config_id, cfg.total_days
                ),
                -- Add standard deviation metric
                average_max_stddev AS (
                    SELECT
                      *,
                      -- For days without consumption, fill with daily consumption of 0
                      (SELECT stddev(e) FROM
                         unnest(array_cat(
                            daily_consumption_arr,
                            ARRAY(SELECT 0.0 FROM generate_series(1, total_days - count_days))
                         )) AS e)
                      AS daily_standard_deviation
                    FROM average_max
                )
                -- Collect data for the materialized view
                SELECT
                    row_number() over (order by cfg.id, metrics.product_id) as id,
                    cfg.id AS config_id,
                    cfg.date_from,
                    cfg.date_to,
                    cfg.warehouse_id,
                    cfg.location_id,
                    cfg.abc_classification_level,
                    metrics.product_id,
                    metrics.average_qty_by_consumption,
                    metrics.average_amount AS average_daily_consumption_count,
                    metrics.daily_max_qty AS max_daily_qty,
                    metrics.daily_average_qty AS average_daily_qty,
                    metrics.total_amount AS nbr_consumptions,
                    pt.sale_ok,
                    pt.is_mto,
                    metrics.daily_standard_deviation
                    FROM average_max_stddev metrics
                    JOIN cfg ON cfg.id = metrics.config_id
                    JOIN product_product pp ON pp.id = metrics.product_id
                    JOIN product_template pt ON pt.id = pp.product_tmpl_id
                ) WITH NO DATA;""",  # noqa: B950
            {
                "table": AsIs(self._table),
                "now": now,
            },
        )
        self.env.cr.execute(
            "CREATE UNIQUE INDEX pk_%s ON %s (id)",
            (AsIs(self._table), AsIs(self._table)),
        )
        for name, field in self._fields.items():
            if not field.index:
                continue
            self.env.cr.execute(
                "CREATE INDEX %s_%s_idx ON %s (%s)",
                (AsIs(self._table), AsIs(name), AsIs(self._table), AsIs(name)),
            )
        self.set_refresh_date(date=False)
        cron = self.env.ref(
            "stock_average_daily_sale.refresh_materialized_view",
            # at install, won't exist yet
            raise_if_not_found=False,
        )
        # refresh data asap, but not during the upgrade
        if cron:
            cron.nextcall = fields.Datetime.now()

    def init(self):
        self._create_materialized_view()
