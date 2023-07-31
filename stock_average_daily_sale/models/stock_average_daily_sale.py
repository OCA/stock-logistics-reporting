# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from psycopg2.errors import ObjectNotInPrerequisiteState
from psycopg2.extensions import AsIs

from odoo import _, api, fields, models

from odoo.addons.stock_storage_type_putaway_abc.models.stock_location import (
    ABC_SELECTION,
)

_logger = logging.getLogger(__name__)


class StockAverageDailySale(models.Model):

    _name = "stock.average.daily.sale"
    _auto = False
    _order = "abc_classification_level ASC, product_id ASC"
    _description = "Average Daily Sale for Products"

    abc_classification_profile_id = fields.Many2one(
        comodel_name="abc.classification.profile",
        required=True,
        index=True,
    )
    abc_classification_level = fields.Selection(
        selection=ABC_SELECTION, required=True, readonly=True, index=True
    )
    average_daily_sales_count = fields.Float(
        required=True,
        digits="Product Unit of Measure",
        help="How much deliveries on average for this product on the period. "
        "The spikes are excluded from the average computation.",
    )
    average_qty_by_sale = fields.Float(
        required=True,
        digits="Product Unit of Measure",
        help="The quantity "
        "delivered on average for one delivery of this product on the period. "
        "The spikes are excluded from the average computation.",
    )
    average_daily_qty = fields.Float(
        digits="Product Unit of Measure",
        required=True,
        help="The quantity delivered on average on one day for this product on "
        "the period. The spikes are excluded from the average computation.",
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
        help="Safety stock to cover the variability of the quantity delivered "
        "each day. Formula: daily standard deviation * safety factor * sqrt(nbr days in the period)",
    )
    recommended_qty = fields.Float(
        required=True,
        digits="Product Unit of Measure",
        help="Minimal recommended quantity in stock. Formula: average daily qty * number days in stock + safety",
    )
    sale_ok = fields.Boolean(
        string="Can be Sold",
        readonly=True,
        index=True,
        help="Specify if the product can be selected in a sales order line.",
    )
    standard_deviation = fields.Float(string="Qty Standard Deviation", required=True)
    daily_standard_deviation = fields.Float(
        string="Daily Qty Standard Deviation", required=True
    )
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", required=True)
    qty_in_stock = fields.Float(
        string="Quantity in stock",
        digits="Product Unit of Measure",
        help="All stock locations, reserved product included",
        required=True,
    )

    @api.model
    def _check_view(self):
        try:
            self.env.cr.execute("SELECT COUNT(1) FROM %s", (AsIs(self._table),))
            return True
        except ObjectNotInPrerequisiteState:
            _logger.warning(
                _("The materialized view has not been populated. Launch the cron.")
            )
            return False
        except Exception as e:
            raise e

    # pylint: disable=redefined-outer-name
    @api.model
    def search_read(
        self, domain=None, fields=None, offset=0, limit=None, order=None, **read_kwargs
    ):
        if not self._check_view():
            return self.browse()
        return super().search_read(
            domain=domain,
            fields=fields,
            offset=offset,
            limit=limit,
            order=order,
            **read_kwargs
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
        self.env.cr.execute("refresh materialized view %s", (AsIs(self._table),))
        self.set_refresh_date()

    def _create_materialized_view(self):
        self.env.cr.execute(
            "DROP MATERIALIZED VIEW IF EXISTS %s CASCADE", (AsIs(self._table),)
        )
        self.env.cr.execute(
            """
            CREATE MATERIALIZED VIEW %(table)s AS (
            -- Create a consolidated definition of parameters used into the average daily
            -- sales computation. Parameters are specified by product ABC class
                WITH cfg AS (
                    SELECT
                        *,
                        -- end of the analyzed period
                        NOW()::date - '1 day'::interval as date_to,
                        -- start of the analyzed period computed from the original cfg
                        (NOW() - (period_value::TEXT || ' ' || period_name::TEXT)::INTERVAL):: date as date_from,
                        -- the number of business days between start and end computed by
                        -- removing saturday and sunday
                        (SELECT count(1) from (select EXTRACT(DOW FROM s.d::date) as dd
                            FROM generate_series(
                            (NOW() - (period_value::TEXT || ' ' || period_name::TEXT)::INTERVAL):: date ,
                            (NOW()- '1 day'::interval)::date,
                            '1 day') AS s(d)) t
                            WHERE dd not in(0,6)) AS nrb_days_without_sat_sun
                    FROM
                        stock_average_daily_sale_config
                ),
                -- Create a consolidated view of all the stock moves from internal locations
                -- to customer location. The consolidation is done by including all the moves
                -- with a date done into the period provided by the configuration for each
                -- product according to its abc classification.
                -- The consolidated view also include the standard deviation of the product qty
                -- sold at once, and the lower and upper bounds to use to exclude qties
                -- that diverge too much from the average qty by product. The factor applied
                -- to the standard deviation to compute the lower and upper bounds is also
                -- provided by the configuration according the product's abc classification
                -- All the products without abc classification are linked to the 'C' class
                deliveries_last AS (
                    SELECT
                        sm.product_id,
                        sm.product_uom_qty,
                        sl_src.warehouse_id,
                        (avg(product_uom_qty) OVER pid
                            - (stddev_samp(product_uom_qty) OVER pid * cfg.standard_deviation_exclude_factor)
                        )  as lower_bound,
                        (avg(product_uom_qty) OVER pid
                            + ( stddev_samp(product_uom_qty) OVER pid * cfg.standard_deviation_exclude_factor)
                        ) as upper_bound,
                        coalesce ((stddev_samp(product_uom_qty) OVER pid), 0) as standard_deviation,
                        cfg.nrb_days_without_sat_sun,
                        cfg.date_from,
                        cfg.date_to,
                        cfg.id as config_id,
                        sm.date
                    FROM stock_move sm
                        JOIN stock_location sl_src ON sm.location_id = sl_src.id
                        JOIN stock_location sl_dest ON sm.location_dest_id = sl_dest.id
                        JOIN product_product pp on pp.id = sm.product_id
                        JOIN product_template pt on pp.product_tmpl_id = pt.id
                        JOIN cfg on cfg.abc_classification_level = coalesce(pt.abc_storage, 'c')
                    WHERE
                        sl_src.usage in ('view', 'internal')
                        AND sl_dest.usage = 'customer'
                        AND sm.date BETWEEN cfg.date_from AND cfg.date_to
                        AND sm.state = 'done'
                    WINDOW pid AS (PARTITION BY sm.product_id, sm.warehouse_id)
                ),

                averages AS(
                    SELECT
                        concat(warehouse_id, product_id)::integer as id,
                        product_id,
                        warehouse_id,
                        (avg(product_uom_qty) FILTER
                            (WHERE product_uom_qty BETWEEN lower_bound AND upper_bound OR standard_deviation = 0)
                            )::numeric AS average_qty_by_sale,
                        (count(product_uom_qty) FILTER
                            (WHERE product_uom_qty BETWEEN lower_bound AND upper_bound OR standard_deviation = 0)
                            / nrb_days_without_sat_sun::numeric) AS average_daily_sales_count,
                        count(product_uom_qty) FILTER
                            (WHERE product_uom_qty BETWEEN lower_bound AND upper_bound OR standard_deviation = 0)::double precision as nbr_sales,
                        standard_deviation::numeric ,
                        date_from,
                        date_to,
                        config_id,
                        nrb_days_without_sat_sun
                    FROM deliveries_last
                    GROUP BY product_id, warehouse_id, standard_deviation, nrb_days_without_sat_sun, date_from, date_to, config_id
                ),
                -- Compute the stock by product in locations under stock
                stock_qty AS (
                    SELECT sq.product_id AS pp_id,
                        sum(sq.quantity) AS qty_in_stock,
                        sl.warehouse_id AS warehouse_id
                        FROM stock_quant sq
                        JOIN stock_location sl ON sq.location_id = sl.id
                        JOIN stock_warehouse sw ON sl.warehouse_id = sw.id
                        WHERE sl.parent_path LIKE concat('%%/', sw.average_daily_sale_root_location_id, '/%%')
                        GROUP BY sq.product_id, sl.warehouse_id
                ),
                -- Compute the standard deviation of the average daily sales count
                -- excluding saturday and sunday
                daily_standard_deviation AS(
                    SELECT
                        id,
                        product_id,
                        warehouse_id,
                        stddev_samp(daily_sales) as daily_standard_deviation
                        from (
                            SELECT
                                to_char(date_trunc('day', date), 'YYYY-MM-DD'),
                                concat(warehouse_id, product_id)::integer as id,
                                product_id,
                                warehouse_id,
                                (count(product_uom_qty) FILTER
                                    (WHERE product_uom_qty BETWEEN lower_bound AND upper_bound OR standard_deviation = 0)
                                ) as daily_sales
                            FROM deliveries_last
                            WHERE EXTRACT(DOW FROM date) <> '0' AND EXTRACT(DOW FROM date) <> '6'
                            GROUP BY product_id, warehouse_id, 1
                        ) as averages_daily group by id, product_id, warehouse_id

                )

                -- Collect the data for the materialized view
                    SELECT
                        t.id,
                        t.product_id,
                        t.warehouse_id,
                        average_qty_by_sale,
                        average_daily_sales_count,
                        average_qty_by_sale * average_daily_sales_count as average_daily_qty,
                        nbr_sales,
                        standard_deviation,
                        date_from,
                        date_to,
                        config_id,
                        abc_classification_level,
                        cfg.abc_classification_profile_id,
                        sale_ok,
                        is_mto,
                        sqty.qty_in_stock as qty_in_stock,
                        ds.daily_standard_deviation,
                        ds.daily_standard_deviation * cfg.safety_factor * sqrt(nrb_days_without_sat_sun) as safety,
                        (cfg.number_days_qty_in_stock * average_qty_by_sale * average_daily_sales_count) + (ds.daily_standard_deviation * cfg.safety_factor * sqrt(nrb_days_without_sat_sun)) as safety_bin_min_qty_new,
                        cfg.number_days_qty_in_stock * GREATEST(average_daily_sales_count, 1)  * (average_qty_by_sale + (standard_deviation * cfg.safety_factor)) as safety_bin_min_qty_old,
                        GREATEST(
                            (cfg.number_days_qty_in_stock * average_qty_by_sale * average_daily_sales_count) + (ds.daily_standard_deviation * cfg.safety_factor * sqrt(nrb_days_without_sat_sun)),
                            (cfg.number_days_qty_in_stock *  average_qty_by_sale)
                        ) as recommended_qty
                    FROM averages t
                    JOIN daily_standard_deviation ds on ds.id= t.id
                    JOIN stock_average_daily_sale_config cfg on cfg.id = t.config_id
                    JOIN stock_qty sqty on sqty.pp_id = t.product_id AND t.warehouse_id = sqty.warehouse_id
                    JOIN product_product pp on pp.id = t.product_id
                    JOIN product_template pt on pt.id = pp.product_tmpl_id
                    ORDER BY product_id
                ) WITH NO DATA;""",
            {
                "table": AsIs(self._table),
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
