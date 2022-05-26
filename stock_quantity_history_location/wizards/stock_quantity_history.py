# Copyright 2019 ForgeFlow S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockQuantityHistory(models.TransientModel):
    _inherit = "stock.quantity.history"

    location_id = fields.Many2one(
        "stock.location", domain=[("usage", "in", ["internal", "transit"])]
    )
    include_child_locations = fields.Boolean("Include child locations", default=True)

    def open_at_date(self):
        action = super(StockQuantityHistory, self).open_at_date()
        ctx = action["context"]
        if self.location_id:
            ctx["location"] = self.location_id.id
            ctx["compute_child"] = self.include_child_locations
            if ctx.get("company_owned", False):
                ctx.pop("company_owned")
            action["name"] = "{} ({})".format(
                action["name"], self.location_id.complete_name
            )
            action["context"] = ctx
        return action
