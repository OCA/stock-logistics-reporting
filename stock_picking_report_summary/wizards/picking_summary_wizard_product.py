# Copyright (C) 2015 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PickingSummaryWizardProduct(models.TransientModel):
    _name = "picking.summary.wizard.product"
    _description = "Picking Summary Wizard Product"

    wizard_id = fields.Many2one(comodel_name="picking.summary.wizard")

    product_id = fields.Many2one(comodel_name="product.product")

    quantity_total = fields.Float()

    standard_price = fields.Float(
        related="product_id.standard_price", digits="Product Price"
    )

    standard_price_total = fields.Float(
        compute="_compute_standard_price_total",
        digits="Product Price",
    )

    def _compute_standard_price_total(self):
        for line in self:
            line.standard_price_total = (
                line.product_id.standard_price * line.quantity_total
            )
