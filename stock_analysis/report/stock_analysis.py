# © 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import tools
from odoo import models, fields, api


class StockAnalysis(models.Model):
    _name = 'stock.analysis'
    _auto = False
    _rec_name = 'product_id'
    _description = 'Stock analysis view'

    product_id = fields.Many2one(
        'product.product', string='Product', readonly=True)
    location_id = fields.Many2one(
        'stock.location', string='Location', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)
    lot_id = fields.Many2one(
        'stock.production.lot', string='Lot', readonly=True)
    package_id = fields.Many2one(
        'stock.quant.package', string='Package', readonly=True)
    in_date = fields.Datetime('Incoming Date', readonly=True)
    categ_id = fields.Many2one(
        'product.category', string='Category', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """CREATE or REPLACE VIEW %s as (
            SELECT
                quant.id AS id,
                quant.product_id AS product_id,
                quant.location_id AS location_id,
                quant.quantity AS quantity,
                quant.lot_id AS lot_id,
                quant.package_id AS package_id,
                quant.in_date AS in_date,
                quant.company_id,
                template.categ_id AS categ_id
            FROM stock_quant AS quant
            JOIN product_product prod ON prod.id = quant.product_id
            JOIN product_template template
                ON template.id = prod.product_tmpl_id
            )"""
            % (self._table)
        )
