# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_id = fields.Many2one(index=True)
    unit_price = fields.Float(compute="_compute_unit_price")

    def _compute_unit_price(self):
        for rec in self:
            if rec.quantity:
                rec.unit_price = rec.balance / rec.quantity
            else:
                rec.unit_price = rec.product_id.standard_price
