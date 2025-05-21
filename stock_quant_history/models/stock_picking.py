# Copyright 2025 Foodles (https://www.foodles.co/).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_stock_quant_history(self):
        """Get the last stock quant history related to this picking.
        The picking must be done.
        :return: stock.quant.history recordset"""
        self.ensure_one()
        history_model = self.env["stock.quant.history"]
        if self.state == "done" and self.date_done:
            domain = [
                ("inventory_date", ">=", self.date_done),
                ("product_id", "in", self.move_line_ids.mapped("product_id").ids),
                "|",
                ("lot_id", "in", self.move_line_ids.mapped("lot_id").ids),
                ("lot_id", "=", False),
            ]
            return history_model.search(domain)
        return history_model

    def action_toggle_is_locked(self):
        # Ensure the picking is allowed to be unlocked before toggling the lock status.
        self.check_unlock_allowed()
        return super().action_toggle_is_locked()

    def check_unlock_allowed(self):
        """Check if the picking can be unlocked.
        :return: True if the picking can be unlocked
        :raises ValidationError: if not allowed to unlock"""
        self.ensure_one()
        if self.is_locked:
            history_lines = self.get_stock_quant_history()
            if history_lines.exists():
                snapshot_text = "\n - ".join(
                    history_lines.mapped("snapshot_id").mapped("display_name")
                )
                raise ValidationError(
                    _(
                        "You cannot unlock '%(name)s' because it has related"
                        " stock quant history:\n - %(snapshot_text)s"
                    )
                    % {
                        "name": self.display_name,
                        "snapshot_text": snapshot_text,
                    }
                )
        return True

    def write(self, vals):
        # Constraint the lock status to avoid unlocking a record when a related quant
        # history exists.
        # An unlock action is propagated
        if "is_locked" in vals and not vals.get("is_locked"):
            # Reducing to locked status and done picking
            for picking in self.filtered(
                lambda pick: pick.is_locked and pick.state == "done" and pick.date_done
            ):
                picking.check_unlock_allowed()
        return super().write(vals)
