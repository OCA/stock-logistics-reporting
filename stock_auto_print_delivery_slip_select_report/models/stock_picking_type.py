# Copyright 2026 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    @api.model
    def _default_delivery_slip_report_id(self):
        return self.env.ref("stock.action_report_delivery", raise_if_not_found=False)

    delivery_slip_report_id = fields.Many2one(
        comodel_name="ir.actions.report",
        string="Delivery Slip Report to auto-print",
        domain=[("model", "=", "stock.picking")],
        default=lambda self: self._default_delivery_slip_report_id(),
        help="Report printed when a picking of this type is validated and "
        "'Auto Print Delivery Slip' is enabled. If empty, the standard delivery "
        "slip is printed.",
    )
