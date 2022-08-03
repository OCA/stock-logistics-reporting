# Copyright 2019-22 ForgeFlow, S.L.
# Copyright 2019 Aleph Objects, Inc.
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import ast

from odoo import models


class StockQuantityHistory(models.TransientModel):
    _inherit = "stock.quantity.history"

    def open_at_date(self):
        action = super().open_at_date()
        ctx = action["context"]
        if isinstance(ctx, str):
            ctx = ast.literal_eval(ctx)
        if self.location_id:
            ctx["location"] = self.location_id.id
            ctx["compute_child"] = self.include_child_locations
            if ctx.get("company_owned", False):
                ctx.pop("company_owned")
            # Ensure the context isn't added later and catch it
            ctx["drop_company_owned"] = True
            action["name"] = "%s (%s)" % (
                action["name"],
                self.location_id.complete_name,
            )
            action["context"] = ctx
        return action
