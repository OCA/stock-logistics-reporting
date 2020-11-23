# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
#   (<https://www.eficent.com>)
# Copyright 2018 Aleph Objects, Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _get_all_base_domain(self, company_id=False):
        # Domain:
        # - state is done
        # Then, either 'in' or 'out' moves.
        # 'in' moves:
        # - coming from a location without company, or an inventory location within the same company
        # - going to a location within the same company
        # 'out' moves:
        # - coming from to a location within the same company
        # - going to a location without company, or an inventory location within the same company
        domain = [
            ('state', '=', 'done'),
            '|',
                '&',
                    '|',
                        ('location_id.company_id', '=', False),
                        '&',
                            ('location_id.usage', 'in', ['inventory', 'production']),
                            ('location_id.company_id', '=', company_id or self.env.user.company_id.id),
                    ('location_dest_id.company_id', '=', company_id or self.env.user.company_id.id),
                '&',
                    ('location_id.company_id', '=', company_id or self.env.user.company_id.id),
                    '|',
                        ('location_dest_id.company_id', '=', False),
                        '&',
                            ('location_dest_id.usage', 'in', ['inventory', 'production']),
                            ('location_dest_id.company_id', '=', company_id or self.env.user.company_id.id),
        ]
        return domain
