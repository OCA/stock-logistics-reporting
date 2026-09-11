# Copyright 2026 NICO SOLUTIIONS - ENGERINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_aggregated_product_quantities(self, **kwargs):
        aggregated = super()._get_aggregated_product_quantities(**kwargs)
        for values in aggregated.values():
            product = values.get("product")
            if product:
                values["barcode"] = product.barcode
        return aggregated
