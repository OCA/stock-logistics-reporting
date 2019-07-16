# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import ast
from odoo import models


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    def open_table(self):
        action = super(StockQuantityHistory, self).open_table()
        # Show 0 quantities on Inventory Valuation to display Account Valuation
        # anomalies, such as, non 0 stock_value on cost_method FIFO
        if self.env.context.get('valuation') and not self.location_id:
            domain = ast.literal_eval(action['domain'])
            domain.pop(domain.index(('qty_available', '!=', 0)))
            action['domain'] = domain
        return action
