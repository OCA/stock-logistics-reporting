# Copyright (C) 2022 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    print_summary_extra_info = fields.Html(
        string="Extra Information Printed on Summary",
        compute="_compute_print_summary_extra_info",
    )

    @api.multi
    def _compute_print_summary_extra_info(self):
        # Overload this function to display extra text on
        # picking summary report
        for picking in self:
            picking.print_summary_extra_info = picking.note
