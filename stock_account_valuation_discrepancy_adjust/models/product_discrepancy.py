# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ProductDiscrepancy(models.TransientModel):

    _name = "product.discrepancy"
    _description = "Product Discrepancies"

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
        readonly=True,
    )
    categ_id = fields.Many2one(
        comodel_name="product.category",
        string="Category",
        required=True,
        readonly=True,
    )
    stock_value = fields.Float(string="Inventory Value", readonly=True)
    account_value = fields.Float(string="Accounting Value", readonly=True)
    qty_at_date = fields.Float(string="Inventory Quantity", readonly=True)
    account_qty_at_date = fields.Float(
        string="Accounting Quantity", readonly=True
    )
    valuation_discrepancy = fields.Float(
        string="Valuation discrepancy", readonly=True
    )
    qty_discrepancy = fields.Float(
        string="Quantity discrepancy", readonly=True
    )

    to_date_valuation = fields.Datetime(
        string="To Date Valuation", readonly=True
    )
