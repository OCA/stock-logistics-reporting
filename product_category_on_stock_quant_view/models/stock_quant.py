# Copyright 2016 Panca Putra Pakpahan - PT Solusi Aglis Indonesia <ppakpahan@solusiaglis.co.id>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    product_categ_id = fields.Many2one(related="product_tmpl_id.categ_id")
