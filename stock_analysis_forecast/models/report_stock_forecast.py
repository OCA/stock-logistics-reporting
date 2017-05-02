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
    categ_id = fields.Many2one(
        'product.category', string='Category', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_stock_forecast')
        cr.execute("""CREATE OR REPLACE VIEW report_stock_forecast AS (SELECT
        MIN(FINAL.id) AS id,
        product_id AS product_id,
        date AS date,
        sum(product_qty) AS quantity,
        sum(in_quantity) AS incoming_quantity,
        sum(out_quantity) AS outgoing_quantity,
        location_id,
        categ.id AS categ_id
        FROM
        (SELECT
        MIN(id) AS id,
        MAIN.product_id AS product_id,
        MAIN.product_tmpl_id as product_tmpl_id,
        MAIN.location_id AS location_id,
        MAIN.date AS date,
        sum(MAIN.product_qty) AS product_qty,
        sum(MAIN.in_quantity) AS in_quantity,
        sum(MAIN.out_quantity) AS out_quantity
        FROM
        (SELECT
            MIN(sq.id) AS id,
            sq.product_id,
            product_product.product_tmpl_id,
            date_trunc(
                'day',
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
            GROUP BY date, sq.product_id, sq.location_id,
                     product_product.product_tmpl_id
            UNION ALL
            SELECT
            MIN(-sm.id) AS id,
            sm.product_id,
            product_product.product_tmpl_id,
            date_trunc(
                'day',
                to_date(to_char(sm.date_expected, 'YYYY/MM/DD'),
                'YYYY/MM/DD'))
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
            GROUP BY sm.date_expected, sm.product_id, dest_location.id,
                     product_product.product_tmpl_id
            UNION ALL
            SELECT
                MIN(-sm.id) AS id,
                sm.product_id,
                product_product.product_tmpl_id,
                date_trunc(
                        'day',
                        to_date(to_char(sm.date_expected, 'YYYY/MM/DD'),
                        'YYYY/MM/DD'))
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
            GROUP BY sm.date_expected, sm.product_id, source_location.id,
                     product_product.product_tmpl_id)
         AS MAIN
    GROUP BY MAIN.product_id, MAIN.date, MAIN.location_id, MAIN.product_tmpl_id
    ) AS FINAL
    JOIN product_template tmpl ON FINAL.product_tmpl_id = tmpl.id
    JOIN product_category categ ON tmpl.categ_id = categ.id
    GROUP BY product_id, date, location_id, categ.id)""")
