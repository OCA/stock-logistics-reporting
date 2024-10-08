# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

from odoo.addons.web.controllers.main import clean_action

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()
        # Determine if res contains the report reception action to launch after
        # pdf downloaded
        auto_print_stock_reception_report = False
        if (
            isinstance(res, dict)
            and res.get("xml_id", False) == "stock.stock_reception_action"
        ):
            auto_print_stock_reception_report = True
        if res is True or auto_print_stock_reception_report:
            report_actions = self._get_autoprint_report_actions()
            return self._auto_print_on_validate(
                report_actions, res if auto_print_stock_reception_report else False
            )
        return res

    @api.model
    def _auto_print_on_validate(self, reports, other_action=False):
        report_action_list = []
        if other_action:
            report_action_list = reports + [other_action]
        else:
            report_action_list = reports + [
                {"type": "ir.actions.act_window_close"},
                {"type": "ir.actions.client", "tag": "reload"},
            ]
        return {"type": "ir.actions.act_multi", "actions": report_action_list}

    def _get_autoprint_report_actions(self):
        report_actions = []
        pickings_to_print = self.filtered(
            lambda p: p.picking_type_id.auto_print_delivery_slip
        )
        if pickings_to_print:
            action = self.env.ref("stock.action_report_delivery").report_action(
                pickings_to_print.ids, config=False
            )
            clean_action(action, self.env)
            report_actions.append(action)
        return report_actions
