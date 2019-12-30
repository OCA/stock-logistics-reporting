# Copyright 2019 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_domain_locations(self):
        """Ensures the location context isn't overriden"""
        ctx = dict(self.env.context)
        if not ctx.get('drop_company_owned') or not ctx.get('company_owned'):
            return super()._get_domain_locations()
        ctx.pop('company_owned', None)
        self_ctx = self.with_context(ctx)
        return super(ProductProduct, self_ctx)._get_domain_locations()
