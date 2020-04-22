# Copyright 2020, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class StockKardexReport(models.Model):
    _name = "stock.kardex.report"
    _description = "This model creates a kardex report for stock moves"
    _order = "date desc"

    move_id = fields.Many2one("stock.move", readonly=True)
    product_id = fields.Many2one("product.product", readonly=True)
    product_uom_id = fields.Many2one("uom.uom", readonly=True, string="Unit of Measure")
    lot_id = fields.Many2one("stock.production.lot", readonly=True)
    owner_id = fields.Many2one("res.partner", readonly=True)
    package_id = fields.Many2one("stock.quant.package", readonly=True)
    location_id = fields.Many2one("stock.location", readonly=True)
    location_dest_id = fields.Many2one(
        "stock.location", readonly=True, string="Destination"
    )
    qty_done = fields.Float("Done", readonly=True, digits=(10, 2))
    date = fields.Datetime(readonly=True)
    origin = fields.Char(readonly=True)
    balance = fields.Float(readonly=True, digits=(10, 2))
    cost = fields.Float(readonly=True, digits=(10, 2))
