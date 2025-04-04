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


class StockAverageDailySale(models.Model):
    _name = "stock.average.daily.sale"
    _auto = False
    _order = "abc_classification_level ASC, product_id ASC"
    _description = "Average Daily Sale for Products"

    abc_classification_level = fields.Selection(
        selection=ABC_SELECTION, string="ABC", required=True, readonly=True, index=True
    )
    average_daily_sales_count = fields.Float(
        required=True,
        digits="Product Unit of Measure",
        help="How much deliveries on average for this product on the period.",
    )
    average_qty_by_sale = fields.Float(
        required=True,
        digits="Product Unit of Measure",
        help="The quantity "
        "delivered on average for one delivery of this product on the period.",
    )
    average_daily_qty = fields.Float(
        digits="Product Unit of Measure",
        required=True,
        help="The quantity delivered on average on one day for this product on "
        "the period.",
    )
    max_daily_qty = fields.Float(
        digits="Product Unit of Measure",
        required=True,
        help="The max quantity delivered on one day for this product on the period.",
    )
    config_id = fields.Many2one(
        string="Stock Average Daily Sale Configuration",
        comodel_name="stock.average.daily.sale.config",
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
    nbr_sales = fields.Integer(
        string="Number of Sales",
        required=True,
        help="The total amount of deliveries for this product over the complete period",
    )
    product_id = fields.Many2one(
        comodel_name="product.product", string="Product", required=True, index=True
    )
    safety = fields.Float(
        required=True,
        compute="_compute_safety",
        help="Safety stock to cover the variability of the quantity delivered "
        "each day. Formula: daily standard deviation * safety factor * sqrt(nbr days in the period)",
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
        help="Minimal recommended quantity in stock. Formula: average daily qty * number days in stock + safety",
    )

    def _compute_recommended_qty(self):
        for rec in self:
            lt = rec.config_id.number_days_qty_in_stock
            average_daily = lt * rec.average_daily_qty + rec.safety
            average_sale = lt * rec.average_qty_by_sale
            rec.recommended_qty = max(average_daily, average_sale)

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
            "stock_average_daily_sale_refresh_date"
        )

    @api.model
    def set_refresh_date(self, date=None):
        if date is None:
            date = fields.Datetime.now()
        self.env["ir.config_parameter"].set_param(
            "stock_average_daily_sale_refresh_date", date
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
            """
            CREATE MATERIALIZED VIEW %(table)s AS (
                -- Create a consolidated definition of parameters used into the average daily
                -- sales computation. Parameters are specified by product ABC class
                WITH cfg AS (
                    SELECT
                        stock_average_daily_sale_config.*,
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
                        stock_average_daily_sale_config
                    JOIN stock_location sl ON stock_average_daily_sale_config.location_id = sl.id
                    JOIN LATERAL (
                        SELECT
                        -- start of the analyzed period computed from the original cfg
                        (%(now)s::date - (period_value::text || ' ' || period_name::text)::interval)::date AS date_from,
                        -- end of the analyzed period; don't consider today as we don't have all figures yet
                        (%(now)s::date - '1 day'::interval)::date AS date_to
                    ) dts ON true
                    WHERE
                        stock_average_daily_sale_config.active = True
                ),
                -- Collect all moves from the config location to outside that location
                consumption AS (
                    SELECT
                        sm.product_id,
                        sm.product_uom_qty,
                        cfg.id AS config_id,
                        sm.date::date AS day
                    FROM stock_move sm
                        JOIN stock_location sl_src ON sm.location_id = sl_src.id
                        JOIN stock_location sl_dest ON sm.location_dest_id = sl_dest.id
                        JOIN product_product pp ON pp.id = sm.product_id
                        JOIN product_template pt ON pp.product_tmpl_id = pt.id
                        CROSS JOIN LATERAL (
                            SElECT * FROM cfg
                            WHERE cfg.abc_classification_level = COALESCE(pt.abc_storage, 'c')
                            AND sl_src.parent_path ilike concat(cfg.location_parent_path, '%%')
                            AND sl_dest.parent_path not ilike concat(cfg.location_parent_path, '%%')
                            -- as date is datetime and date_to is a date, we need to add 1 day to include date_to day
                            AND sm.date BETWEEN cfg.date_from AND (cfg.date_to + '1 day'::interval)
                            -- Consumption on excluded days are included
                            -- AND (NOT cfg.exclude_weekends OR EXTRACT(ISODOW FROM sm.date) NOT IN (6,7))
                        ) AS cfg
                    WHERE
                        sm.state = 'done' AND sm.product_uom_qty > 0
                        -- exclude inventory loss
                        AND sl_dest.usage != 'inventory'
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
                        SUM(dc.qty) / SUM(dc.count) AS average_qty_by_sale,
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
                -- Add the standard deviation metric
                average_max_stddev AS(
                    SELECT
                      *,
                      -- For days without consumption, fill with a daily consumption of 0
                      -- The number of missing days is the total days in the period minus days where we have a count
                      -- Combine the array of daily consumption with the 0 and compute standard deviation
                      (SELECT stddev(e) FROM
                         unnest(array_cat(
                            daily_consumption_arr,
                            ARRAY(SELECT 0.0 FROM generate_series(1, total_days - count_days))
                         )) AS e)
                      AS daily_standard_deviation
                    FROM average_max
                )
                -- Collect the data for the materialized view
                SELECT
                    row_number() over (order by cfg.id, metrics.product_id) as id,
                    cfg.id AS config_id,
                    cfg.date_from,
                    cfg.date_to,
                    cfg.warehouse_id,
                    cfg.location_id,
                    cfg.abc_classification_level,
                    metrics.product_id,
                    metrics.average_qty_by_sale,
                    metrics.average_amount AS average_daily_sales_count,
                    metrics.daily_max_qty AS max_daily_qty,
                    metrics.daily_average_qty AS average_daily_qty,
                    metrics.total_amount AS nbr_sales,
                    pt.sale_ok,
                    pt.is_mto,
                    metrics.daily_standard_deviation
                    FROM average_max_stddev metrics
                    JOIN cfg ON cfg.id = metrics.config_id
                    JOIN product_product pp ON pp.id = metrics.product_id
                    JOIN product_template pt ON pt.id = pp.product_tmpl_id
                ) WITH NO DATA;""",
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
