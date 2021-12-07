# Copyright 2019-2021 ForgeFlow S.L.
# Copyright 2019 Aleph Objects, Inc.
from odoo import models, fields, _
from odoo.tools.safe_eval import safe_eval


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries'),
        ], string='Target Moves', default='posted')

    def open_table(self):
        action = super(StockQuantityHistory, self).open_table()
        if self.compute_at_date:
            action['name'] = '%s (%s) %s' % (
                action['name'], self.date, self.target_move == 'posted' and _('All Posted Entries') or _('All Entries'))
        current_context = safe_eval(action['context'])
        current_context.update({
            'target_move': self.target_move,
        })
        action['context'] = current_context
        return action
