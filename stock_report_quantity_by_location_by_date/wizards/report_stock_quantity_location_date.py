# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ReportStockQuantityLocationDate(models.TransientModel):

    _name = "report.stock.quantity.location.date"
    _description = "Stock Quantity Report by Location and Date"

    move_date = fields.Date()
    location_id = fields.Many2one(comodel_name="stock.location")
    company_id = fields.Many2one(
        comodel_name="res.company", related="location_id.company_id"
    )
    product_id = fields.Many2one(comodel_name="product.product")
    quantity = fields.Float()
    wizard_id = fields.Many2one(
        comodel_name="stock.report.quantity.location.date",
        required=True,
        ondelete="cascade",
    )
