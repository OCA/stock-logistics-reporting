# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# Copyright 2019 Aleph Objects, Inc.
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv import expression


class StockQuantityHistory(models.TransientModel):
    _inherit = "stock.quantity.history"

    def open_at_date(self):
        action = super().open_at_date()
        if (
            self.location_id
            and self.env.context.get("active_model") == "stock.valuation.layer"
        ):
            operator = "child_of" if self.include_child_locations else "="
            action["domain"] = expression.AND(
                [
                    action["domain"],
                    [
                        "|",
                        (
                            "stock_move_id.location_dest_id",
                            operator,
                            self.location_id.id,
                        ),
                        (
                            "stock_move_id.location_id",
                            operator,
                            self.location_id.id,
                        ),
                    ],
                ]
            )
            action[
                "display_name"
            ] = f"{self.location_id.complete_name} - {action['display_name']}"
        return action
