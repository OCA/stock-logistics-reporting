# Copyright 2018 Odoo, S.A.
# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo import tools


class ReportStockLinesDate(models.Model):
    _name = "report.stock.lines.date"
    _description = "Dates of Inventories and latest Moves"
    _auto = False
    _order = "date"
    id = fields.Integer('Product Id', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True,
                                 index=True,
                                 )
    date = fields.Datetime('Date of latest Inventory', readonly=True)
    move_date = fields.Datetime('Date of latest Stock Move', readonly=True)
    active = fields.Boolean("Active", readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s as (
            WITH Q1 AS (
                SELECT
                p.id AS id,
                p.id AS product_id,
                max(s.date) AS date,                
                p.active AS active
                FROM
                product_product p
                    LEFT JOIN (
                    stock_inventory_line l
                    INNER JOIN stock_inventory s ON (
                    l.inventory_id=s.id AND s.state = 'done')
                    ) ON (p.id=l.product_id)
                GROUP BY p.id
            ),
            Q2 AS (
                SELECT 
                p.id AS id,
                p.id AS product_id,
                max(m.date) AS move_date,
                p.active AS active
                FROM
                product_product p
                    LEFT JOIN stock_move m ON (m.product_id=p.id
                    AND m.state = 'done')
                GROUP BY p.id
            )
            SELECT
                p.id AS id,
                p.id AS product_id,
                max(Q1.date) AS date,
                max(Q2.move_date) AS move_date,
                p.active AS active
            FROM
            product_product p
                LEFT JOIN Q1 ON Q1.id = p.id
                LEFT JOIN Q2 ON Q2.id = p.id
            GROUP BY p.id)
        """ % (self._table, ))
