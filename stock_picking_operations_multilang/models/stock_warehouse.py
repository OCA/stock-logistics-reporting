# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    @api.model
    def _lang_get(self):
        return self.env["res.lang"].get_installed()

    picking_operation_language_option = fields.Selection(
        [("partner", "Partner"), ("warehouse", "Warehouse")],
        help="Partner: Picking Operations report will use the partner's language.\n"
        "Warehouse: Picking Operations report will use the language specified in "
        "the Warehouse Language field.",
    )

    warehouse_language = fields.Selection(
        _lang_get,
        default=lambda self: self.env.lang,
    )
    active_lang_count = fields.Integer(compute="_compute_active_lang_count")

    @api.depends("warehouse_language")
    def _compute_active_lang_count(self):
        lang_count = len(self.env["res.lang"].get_installed())
        for rec in self:
            rec.active_lang_count = lang_count
