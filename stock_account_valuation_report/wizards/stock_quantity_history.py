# Copyright 2019-2021 ForgeFlow S.L.
# Copyright 2019 Aleph Objects, Inc.
from odoo import models, fields, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import format_date


class StockQuantityHistory(models.TransientModel):
    _inherit = "stock.quantity.history"

    target_move = fields.Selection(
        [
            ("posted", "All Posted Entries"),
            ("all", "All Entries"),
        ],
        string="Target Moves",
        default="posted",
    )

    def open_table(self):
        action = super(StockQuantityHistory, self).open_table()
        if self.compute_at_date:
            action["display_name"] = "%s (%s) %s" % (
                action["display_name"],
                format_date(self.env, fields.Datetime.context_timestamp(self.env.user, self.date)),
                self.target_move == "posted"
                and _("All Posted Entries")
                or _("All Entries"),
            )
        else:
            action["display_name"] = "%s - %s" % (
                action["display_name"],
                self.target_move == "posted"
                and _("All Posted Entries")
                or _("All Entries"),
            )
        current_context = isinstance(action["context"], str) and safe_eval(action["context"]) or action["context"]
        current_context.update(
            {
                "target_move": self.target_move,
            }
        )
        action["context"] = current_context
        return action
