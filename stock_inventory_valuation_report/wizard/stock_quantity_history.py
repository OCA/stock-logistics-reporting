# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class StockQuantityHistory(models.TransientModel):
    _inherit = "stock.quantity.history"

    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            "stock_inventory_valuation_report."
            "action_stock_inventory_valuation_report_html"
        )
        vals = action.read()[0]
        new_context = vals.get("context", {})
        if isinstance(new_context, str):
            try:
                new_context = safe_eval(new_context)
            except (TypeError, SyntaxError, NameError, ValueError):
                _logger.warning(
                    _("Failed context evaluation: %(context)s", context=new_context)
                )
                new_context = {}
        model = self.env["report.stock.inventory.valuation.report"]
        report = model.create(self._prepare_stock_inventory_valuation_report())
        new_context.update(active_id=report.id, active_ids=report.ids)
        vals["context"] = new_context
        return vals

    def button_export_pdf(self):
        self.ensure_one()
        return self._export(report_type="qweb-pdf")

    def button_export_xlsx(self):
        self.ensure_one()
        return self._export(report_type="xlsx")

    def _prepare_stock_inventory_valuation_report(self):
        self.ensure_one()
        vals = {
            "company_id": self.env.user.company_id.id,
        }
        if self.inventory_datetime:
            vals["inventory_datetime"] = self.inventory_datetime
        return vals

    def _export(self, report_type):
        model = self.env["report.stock.inventory.valuation.report"]
        report = model.create(self._prepare_stock_inventory_valuation_report())
        return report.print_report(report_type)
