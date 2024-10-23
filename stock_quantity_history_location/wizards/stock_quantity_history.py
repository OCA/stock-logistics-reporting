# Copyright 2019 ForgeFlow S.L.
# Copyright 2019 Aleph Objects, Inc.
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class StockQuantityHistory(models.TransientModel):
    _inherit = "stock.quantity.history"

    location_id = fields.Many2one(
        "stock.location", domain=[("usage", "in", ["internal", "transit"])]
    )
    include_child_locations = fields.Boolean(default=True)

    def open_at_date(self):
        action = super().open_at_date()
        ctx = action["context"]
        ctx = safe_eval(ctx) if isinstance(ctx, str) else ctx
        if self.location_id:
            ctx["location"] = self.location_id.id
            ctx["compute_child"] = self.include_child_locations
            if ctx.get("company_owned", False):
                ctx.pop("company_owned")
            action[
                "display_name"
            ] = f"{self.location_id.complete_name} - {action['display_name']}"
            action["context"] = ctx
        return action
