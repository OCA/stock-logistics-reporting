# Copyright 2019-21 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockReportQuantityByLocation(models.TransientModel):
    _name = "stock.report.quantity.by.location"
    _description = "Stock Report By Location"

    wiz_id = fields.Many2one(comodel_name="stock.report.quantity.by.location.prepare")
    product_id = fields.Many2one(comodel_name="product.product", required=True)
    product_category_id = fields.Many2one(
        comodel_name="product.category", string="Product Category"
    )
    location_id = fields.Many2one(comodel_name="stock.location", required=True)
    quantity_on_hand = fields.Float(string="Qty On Hand")
    quantity_reserved = fields.Float(string="Qty Reserved")
    quantity_unreserved = fields.Float(string="Qty Unreserved")
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Product UoM")
    default_code = fields.Char("Internal Reference")
