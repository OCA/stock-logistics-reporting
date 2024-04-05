# Copyright 2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockQuantHistory(models.Model):
    _name = "stock.quant.history"
    _description = "Stock quants history"
    _order = "snapshot_id, inventory_date, product_id, lot_id, location_id"
    snapshot_id = fields.Many2one(
        comodel_name="stock.quant.history.snapshot",
        ondelete="cascade",
        required=True,
        index=True,
        string="Snapshot settings",
        help="Snapshot settings used to generate this line",
    )
    inventory_date = fields.Datetime(
        related="snapshot_id.inventory_date",
        index=True,
        store=True,
    )

    # same fields as stock.quant
    product_id = fields.Many2one(
        "product.product",
        "Product",
        ondelete="restrict",
        readonly=True,
        required=True,
        index=True,
        check_company=True,
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product Template",
        related="product_id.product_tmpl_id",
        readonly=True,
    )
    product_uom_id = fields.Many2one(
        "uom.uom", "Unit of Measure", readonly=True, related="product_id.uom_id"
    )
    company_id = fields.Many2one(
        related="location_id.company_id", string="Company", store=True, readonly=True
    )
    location_id = fields.Many2one(
        "stock.location",
        "Location",
        auto_join=True,
        ondelete="restrict",
        readonly=True,
        required=True,
        index=True,
        check_company=True,
    )
    lot_id = fields.Many2one(
        "stock.production.lot",
        "Lot/Serial Number",
        index=True,
        ondelete="restrict",
        readonly=True,
        check_company=True,
    )
    quantity = fields.Float(
        "Quantity",
        help=(
            "Quantity of products in this quant, "
            "in the default unit of measure of the product"
        ),
        readonly=True,
    )
