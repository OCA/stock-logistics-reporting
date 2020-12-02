# -*- coding: utf-8 -*-
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
#   (<https://www.eficent.com>)
# Copyright 2018 Aleph Objects, Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def _is_in(self):
        # use same approach as found in stock.py in stock_account module
        # _account_entry_move method
        self.ensure_one()
        location_from = self.location_id
        location_to = self.location_dest_id
        company_from = (
            location_from.usage == "internal"
            and location_from.company_id
            or False
        )
        company_to = (
            location_to
            and (location_to.usage == "internal")
            and location_to.company_id
            or False
        )
        return company_to and (
            self.location_id.usage not in ("internal", "transit")
            and self.location_dest_id.usage == "internal"
            or company_from != company_to
        )

    @api.multi
    def _is_out(self):
        # use same approach as found in stock.py in stock_account module
        # _account_entry_move method
        self.ensure_one()
        location_from = self.location_id
        location_to = self.location_dest_id
        company_from = (
            location_from.usage == "internal"
            and location_from.company_id
            or False
        )
        company_to = (
            location_to
            and (location_to.usage == "internal")
            and location_to.company_id
            or False
        )
        return company_from and (
            self.location_id.usage == "internal"
            and self.location_dest_id.usage not in ("internal", "transit")
            or company_from != company_to
        )

    @api.model
    def _get_all_base_domain(self, company_id=False):
        """
        This is a backport of standard Odoo method from v11
        """
        domain = [
            ("state", "=", "done"),
            "|",
            "&",
            "|",
            ("location_id.company_id", "=", False),
            "&",
            ("location_id.usage", "in", ["inventory", "production"]),
            (
                "location_id.company_id",
                "=",
                company_id or self.env.user.company_id.id,
            ),
            (
                "location_dest_id.company_id",
                "=",
                company_id or self.env.user.company_id.id,
            ),
            "&",
            (
                "location_id.company_id",
                "=",
                company_id or self.env.user.company_id.id,
            ),
            "|",
            ("location_dest_id.company_id", "=", False),
            "&",
            ("location_dest_id.usage", "in", ["inventory", "production"]),
            (
                "location_dest_id.company_id",
                "=",
                company_id or self.env.user.company_id.id,
            ),
        ]
        return domain
