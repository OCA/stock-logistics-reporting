# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    demand_period_ids = fields.Many2many(
        "product.demand.period",
        string="Demand periods",
        compute="_compute_demand_period_ids",
        inverse="_inverse_demand_period_ids",
        context={"active_test": False},
    )

    @api.depends("company_id")
    def _compute_demand_period_ids(self):
        self.demand_period_ids = self.env["product.demand.period"].search(
            [("active", "=", True)]
        )

    def _inverse_demand_period_ids(self):
        selected_periods = self.demand_period_ids
        to_activate = self.env["product.demand.period"].search(
            [("active", "=", False), ("id", "in", selected_periods.ids)]
        )
        to_archive = self.env["product.demand.period"].search(
            [("active", "=", True), ("id", "not in", selected_periods.ids)]
        )
        if to_activate:
            to_activate.active = True
        if to_archive:
            to_archive.active = False
