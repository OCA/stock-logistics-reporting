# Copyright 2020 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockMove(models.Model):
    _inherit = ["stock.move", "product.related.filter.mixin"]
    _name = "stock.move"


class StockMoveLine(models.Model):
    _inherit = ["stock.move.line", "product.related.filter.mixin"]
    _name = "stock.move.line"


class StockMoveLine(models.Model):
    _inherit = ["stock.quant", "product.related.filter.mixin"]
    _name = "stock.quant"
