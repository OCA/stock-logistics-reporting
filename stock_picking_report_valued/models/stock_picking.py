# Copyright 2014-2018 Tecnativa - Pedro M. Baeza
# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2016-2022 Tecnativa - Carlos Dauden
# Copyright 2016 Tecnativa - Luis M. Ontalba
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    valued = fields.Boolean(related="partner_id.valued_picking", readonly=True)
    currency_id = fields.Many2one(
        related="sale_id.currency_id",
        readonly=True,
        string="Currency",
        related_sudo=True,  # See explanation for sudo in compute method
    )
    amount_untaxed = fields.Monetary(
        compute="_compute_amount_all",
        string="Untaxed Amount",
        compute_sudo=True,  # See explanation for sudo in compute method
    )
    amount_tax = fields.Monetary(
        compute="_compute_amount_all", string="Taxes", compute_sudo=True
    )
    amount_total = fields.Monetary(
        compute="_compute_amount_all", string="Total", compute_sudo=True
    )

    def _compute_amount_all(self):
        """This is computed with sudo for avoiding problems if you don't have
        access to sales orders (stricter warehouse users, inter-company
        records...).
        """
        for pick in self:
            amount_untaxed = amount_tax = 0.0
            for line in pick.move_line_ids.filtered(lambda ln: ln.state != "cancel"):
                amount_untaxed += line.sale_price_subtotal
                amount_tax += line.sale_price_tax
            pick.update(
                {
                    "amount_untaxed": amount_untaxed,
                    "amount_tax": amount_tax,
                    "amount_total": amount_untaxed + amount_tax,
                }
            )
