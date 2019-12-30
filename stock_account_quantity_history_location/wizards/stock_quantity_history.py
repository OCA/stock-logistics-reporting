# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import ast
from odoo import models


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    def open_table(self):
        """Stock valuation goes by a different path than stock report, so
           we ensure the correct context as well"""
        action = super().open_table()
        if not self.env.context.get('valuation'):
            return action
        # Show 0 quantities on Inventory Valuation to display Account Valuation
        # anomalies, such as, non 0 stock_value on cost_method FIFO
        if not self.location_id:
            domain = ast.literal_eval(action['domain'])
            domain.pop(domain.index(('qty_available', '!=', 0)))
            action['domain'] = domain
        ctx = action['context']
        if isinstance(ctx, str):
            ctx = ast.literal_eval(ctx)
        if self.location_id:
            ctx['location'] = self.location_id.id
            ctx['compute_child'] = self.include_child_locations
            if ctx.get('company_owned', False):
                ctx.pop('company_owned')
            # Ensure the context isn't added later and catch it
            ctx['drop_company_owned'] = True
            action['name'] = '%s (%s)' % (action['name'],
                                          self.location_id.complete_name)
            action['context'] = ctx
        return action
