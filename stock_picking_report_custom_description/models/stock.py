# Copyright 2017 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    several_product_description = fields.Boolean(
        compute='_compute_several_product_description',
    )

    @api.multi
    def _compute_several_product_description(self):
        for operation in self:
            names = operation.mapped('move_id.name')
            operation.several_product_description = (
                not all(x == names[0] for x in names))
