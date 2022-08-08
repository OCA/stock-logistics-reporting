# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# Copyright 2019 Aleph Objects, Inc.
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import ast

from odoo import models
from odoo.osv import expression


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
            if self.env.context.get("active_model") == "stock.valuation.layer":
                action["domain"] = expression.AND(
                    [
                        action["domain"],
                        [("stock_move_id.location_dest_id", "=", self.location_id.id)],
                    ]
                )
        else:
            # Show 0 quantities on Inventory Valuation to display Account Valuation
            # anomalies, such as, non 0 stock_value on cost_method FIFO
            if self.env.context.get("active_model") == "stock.valuation.layer":
                action["domain"] = expression.AND(
                    [action["domain"], [("quantity", "!=", 0)]]
                )
            else:
                action["domain"] = expression.AND(
                    [action["domain"], [("qty_available", "!=", 0)]]
                )
        return action
