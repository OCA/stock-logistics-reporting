# Copyright 2026 Moduon
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _compute_amount_all(self):
        res = super()._compute_amount_all()
        for picking in self:
            fee_lines = picking.sale_id.order_line.filtered(
                lambda x, picking=picking: x.delivery_fee_picking_id == picking
            )
            if not fee_lines:
                continue
            fee_amount_untaxed = sum(fee_lines.mapped("price_subtotal"))
            fee_amount_taxed = sum(fee_lines.mapped("price_tax"))
            fee_amount_total = fee_amount_untaxed + fee_amount_taxed
            picking.update(
                {
                    "amount_untaxed": picking.amount_untaxed + fee_amount_untaxed,
                    "amount_tax": picking.amount_tax + fee_amount_taxed,
                    "amount_total": picking.amount_total + fee_amount_total,
                }
            )
        return res
