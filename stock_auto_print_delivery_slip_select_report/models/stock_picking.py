# Copyright 2026 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models

from odoo.addons.web.controllers.utils import clean_action


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_autoprint_report_actions(self):
        report_actions = super()._get_autoprint_report_actions()
        pickings_to_print = self.filtered(
            lambda p: p.picking_type_id.auto_print_delivery_slip
        )
        if not pickings_to_print:
            return report_actions
        default_report = self.env.ref("stock.action_report_delivery")
        # Replace the standard delivery slip action by one action per selected report
        index = next(
            (
                i
                for i, action in enumerate(report_actions)
                if action.get("report_name") == default_report.report_name
            ),
            None,
        )
        if index is None:
            return report_actions
        delivery_slip_actions = []
        pickings_by_report = pickings_to_print.grouped(
            lambda p: p.picking_type_id.delivery_slip_report_id or default_report
        )
        for report, pickings in pickings_by_report.items():
            action = report.report_action(pickings.ids, config=False)
            clean_action(action, self.env)
            delivery_slip_actions.append(action)
        report_actions[index : index + 1] = delivery_slip_actions
        return report_actions
