# Copyright 2019-21 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class StockReportByLocationPrepare(models.TransientModel):
    _name = "stock.report.quantity.by.location.prepare"
    _description = "Stock Report Quantity By Location Prepare"

    location_ids = fields.Many2many(
        comodel_name="stock.location", string="Locations", required=True
    )
    with_quantity = fields.Boolean(
        string="Quantity > 0",
        default=True,
        help="Show only the products that have existing quantity on hand",
    )

    def open(self):
        self.ensure_one()
        self._compute_stock_report_by_location()
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "pivot,tree",
            "name": _("Stock Report by Location"),
            "context": {
                "search_default_quantity_gt_zero": 1,
                "group_by_no_leaf": 1,
                "group_by": [],
            },
            "res_model": "stock.report.quantity.by.location",
            "domain": [("wiz_id", "=", self.id)],
        }
        return action

    def _compute_stock_report_by_location(self):
        self.ensure_one()
        recs = []
        for loc in self.location_ids:
            quant_groups = self.env["stock.quant"].read_group(
                [("location_id", "child_of", [loc.id])],
                ["quantity", "product_id"],
                ["product_id"],
            )
            mapping = {
                quant_group["product_id"][0]: quant_group["quantity"]
                for quant_group in quant_groups
            }
            products = self.env["product.product"].search([("type", "=", "product")])
            vals_list = []
            for product in products:
                quantity = mapping.get(product.id, 0.0)
                if (self.with_quantity and quantity) or not self.with_quantity:
                    vals_list.append(
                        {
                            "product_id": product.id,
                            "product_category_id": product.categ_id.id,
                            "uom_id": product.uom_id.id,
                            "quantity": mapping.get(product.id, 0.0),
                            "location_id": loc.id,
                            "wiz_id": self.id,
                            "default_code": product.default_code,
                        }
                    )
            recs = self.env["stock.report.quantity.by.location"].create(vals_list)
        return recs.ids


class StockReportQuantityByLocation(models.TransientModel):
    _name = "stock.report.quantity.by.location"
    _description = "Stock Report By Location"

    wiz_id = fields.Many2one(comodel_name="stock.report.quantity.by.location.prepare")
    product_id = fields.Many2one(comodel_name="product.product", required=True)
    product_category_id = fields.Many2one(
        comodel_name="product.category", string="Product Category"
    )
    location_id = fields.Many2one(comodel_name="stock.location", required=True)
    quantity = fields.Float()
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Product UoM")
    default_code = fields.Char("Internal Reference")
