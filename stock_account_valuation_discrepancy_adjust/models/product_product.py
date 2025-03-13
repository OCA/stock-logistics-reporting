from odoo import models
from odoo.tools import float_compare


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _adjustment_needed(self):
        """Check if stock valuation adjustment is needed.

        Returns:
            bool: True if adjustment needed, False otherwise
        """
        self.ensure_one()
        # Prefetch related records
        self = self.with_context(prefetch_fields=True)

        # Get values with prefetch
        qty_compare = float_compare(
            self.qty_at_date,
            self.account_qty_at_date,
            precision_rounding=self.uom_id.rounding,
        )
        value_compare = float_compare(
            self.stock_value,
            self.account_value,
            precision_rounding=self.env.company.currency_id.rounding,
        )
        return not (qty_compare == 0 and value_compare == 0)
