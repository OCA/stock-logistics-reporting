# -*- coding: utf-8 -*-
# Copyright 2016 Odoo SA <https://www.odoo.com>
# Copyright 2016 Alex Comba - Agile Business Group
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models, tools


class ReportStockForecast(models.Model):

    _name = 'report.stock.forecast'
    _description = 'Report Stock Forecast'
    _auto = False

    date = fields.Date(
        string='Date')
    product_id = fields.Many2one(
        'product.product', string='Product', readonly=True)
    quantity = fields.Float(readonly=True)
    incoming_quantity = fields.Float(readonly=True)
    outgoing_quantity = fields.Float(readonly=True)
    location_id = fields.Many2one(
        'stock.location', string='Location', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_stock_forecast')
        cr.execute("""CREATE OR REPLACE VIEW report_stock_forecast AS (SELECT
        MIN(id) AS id,
        product_id AS product_id,
        date AS date,
        sum(product_qty) AS quantity,
        sum(in_quantity) AS incoming_quantity,
        sum(out_quantity) AS outgoing_quantity,
        location_id
        FROM
        (SELECT
        MIN(id) AS id,
        MAIN.product_id AS product_id,
        MAIN.location_id AS location_id,
        SUB.date AS date,
        CASE WHEN MAIN.date = SUB.date
            THEN sum(MAIN.product_qty) ELSE 0 END AS product_qty,
        CASE WHEN MAIN.date = SUB.date
            THEN sum(MAIN.in_quantity) ELSE 0 END AS in_quantity,
        CASE WHEN MAIN.date = SUB.date
            THEN sum(MAIN.out_quantity) ELSE 0 END AS out_quantity
        FROM
        (SELECT
            MIN(sq.id) AS id,
            sq.product_id,
            date_trunc(
                'week',
                to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'),
                'YYYY/MM/DD')) AS date,
            SUM(sq.qty) AS product_qty,
            0 AS in_quantity,
            0 AS out_quantity,
            sq.location_id
            FROM
            stock_quant AS sq
            LEFT JOIN
            product_product ON product_product.id = sq.product_id
            LEFT JOIN
            stock_location location_id ON sq.location_id = location_id.id
            WHERE
            location_id.usage = 'internal'
            GROUP BY date, sq.product_id, sq.location_id
            UNION ALL
            SELECT
            MIN(-sm.id) AS id,
            sm.product_id,
            CASE WHEN sm.date_expected > CURRENT_DATE
            THEN date_trunc(
                'week',
                to_date(to_char(sm.date_expected, 'YYYY/MM/DD'),
                'YYYY/MM/DD'))
            ELSE date_trunc(
                'week',
                to_date(
                    to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) END
            AS date,
            0 AS product_qty,
            SUM(sm.product_qty) AS in_quantity,
            0 AS out_quantity,
            dest_location.id AS location_id
            FROM
               stock_move AS sm
            LEFT JOIN
               product_product ON product_product.id = sm.product_id
            LEFT JOIN
                stock_location dest_location
                ON sm.location_dest_id = dest_location.id
            LEFT JOIN
                stock_location source_location
                ON sm.location_id = source_location.id
            WHERE
                sm.state IN ('confirmed','assigned','waiting') AND
                source_location.usage != 'internal' AND
                dest_location.usage = 'internal'
            GROUP BY sm.date_expected, sm.product_id, dest_location.id
            UNION ALL
            SELECT
                MIN(-sm.id) AS id,
                sm.product_id,
                CASE WHEN sm.date_expected > CURRENT_DATE
                    THEN date_trunc(
                        'week',
                        to_date(to_char(sm.date_expected, 'YYYY/MM/DD'),
                        'YYYY/MM/DD'))
                    ELSE date_trunc(
                        'week',
                        to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'),
                        'YYYY/MM/DD')) END
                AS date,
                0 AS product_qty,
                0 AS in_quantity,
                SUM(sm.product_qty) AS out_quantity,
                source_location.id AS location_id
            FROM
               stock_move AS sm
            LEFT JOIN
               product_product ON product_product.id = sm.product_id
            LEFT JOIN
               stock_location source_location
               ON sm.location_id = source_location.id
            LEFT JOIN
               stock_location dest_location
               ON sm.location_dest_id = dest_location.id
            WHERE
                sm.state IN ('confirmed','assigned','waiting') AND
            source_location.usage = 'internal' AND
            dest_location.usage != 'internal'
            GROUP BY sm.date_expected, sm.product_id, source_location.id)
         AS MAIN
     LEFT JOIN
     (SELECT DISTINCT date
      FROM
      (
             SELECT date_trunc('week', CURRENT_DATE) AS DATE
             UNION ALL
             SELECT date_trunc(
                'week',
                to_date(to_char(sm.date_expected, 'YYYY/MM/DD'),
                'YYYY/MM/DD')) AS date
             FROM stock_move sm
             LEFT JOIN
                stock_location source_location
                ON sm.location_id = source_location.id
             LEFT JOIN
                stock_location dest_location
                ON sm.location_dest_id = dest_location.id
             WHERE
             sm.state IN ('confirmed','assigned','waiting') AND
             sm.date_expected > CURRENT_DATE AND
             ((dest_location.usage = 'internal'
              AND source_location.usage != 'internal')
              OR (source_location.usage = 'internal'
                 AND dest_location.usage != 'internal'))) AS DATE_SEARCH)
             SUB ON (SUB.date IS NOT NULL)
    GROUP BY MAIN.product_id, SUB.date, MAIN.date, MAIN.location_id
    ) AS FINAL
    GROUP BY product_id, date, location_id)""")
