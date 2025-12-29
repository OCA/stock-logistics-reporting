# Copyright 2014-2018 Tecnativa - Pedro M. Baeza
# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2016-2022 Tecnativa - Carlos Dauden
# Copyright 2016 Tecnativa - Luis M. Ontalba
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    valued = fields.Boolean(related="partner_id.valued_picking", readonly=True)
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        compute="_compute_currency_id",
        compute_sudo=True,  # for avoiding access problems
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
            for line in pick.move_line_ids:
                amount_untaxed += line.sale_price_subtotal
                amount_tax += line.sale_price_tax
            pick.update(
                {
                    "amount_untaxed": amount_untaxed,
                    "amount_tax": amount_tax,
                    "amount_total": amount_untaxed + amount_tax,
                }
            )

    @api.depends("sale_id", "sale_id.currency_id", "company_id")
    def _compute_currency_id(self):
        for item in self:
            item.currency_id = item.sale_id.currency_id or item.company_id.currency_id

    def _get_report_valued_total_amount(self):
        """
        Method used by delivery slip reports to get the total amount to be displayed.
        By default, it returns the standard picking total (amount_total).
        Other modules can override this method to add or adjust additional amounts
        (taxes, fees, surcharges, etc.) that must be reflected in the printed
        picking total.
        If the returned value differs from amount_total, the report will display
        the "Total picking" block.
        """
        self.ensure_one()
        return self.amount_total

    def _show_report_valued_total_block(self):
        """
        Return True if the Total Picking block should be displayed in the report.
        The comparison is done using the currency rounding to avoid float
        precision issues.
        """
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        return (
            float_compare(
                self._get_report_valued_total_amount(),
                self.amount_total,
                precision_rounding=currency.rounding,
            )
            != 0
        )
