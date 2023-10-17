# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.tools.safe_eval import safe_eval


class StockQuantityHistory(models.TransientModel):
    _inherit = "stock.quantity.history"

    compute_at_date = fields.Selection(
        [("0", "Current Inventory"), ("1", "At a Specific Date")],
        string="Compute",
        help="Choose to analyze the current inventory or from a specific date in the past.",
        default="0",
    )
    inventory_datetime = fields.Datetime(
        "Inventory at Date",
        help="Choose a date to get the inventory at that date",
        default=fields.Datetime.now,
    )

    def open_table(self):
        self.ensure_one()
        if int(self.compute_at_date):
            tree_view_id = self.env.ref("stock.view_stock_product_tree").id
            form_view_id = self.env.ref("stock.product_form_view_procurement_button").id
            # We pass `to_date` in the context so that `qty_available`
            # will be computed across moves until date.
            return {
                "type": "ir.actions.act_window",
                "views": [(tree_view_id, "tree"), (form_view_id, "form")],
                "view_mode": "tree,form",
                "name": _("Products"),
                "res_model": "product.product",
                "domain": "[('type', '=', 'product')]",
                "context": dict(self.env.context, to_date=self.inventory_datetime),
            }
        else:
            self.env["stock.quant"]._merge_quants()
            self.env["stock.quant"]._unlink_zero_quants()
            return self.env.ref("stock.action_view_quants").read()[0]

    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            "stock_inventory_valuation_report."
            "action_stock_inventory_valuation_report_html"
        )
        vals = action.read()[0]
        context1 = vals.get("context", {})
        if isinstance(context1, str):
            context1 = safe_eval(context1)
        model = self.env["report.stock.inventory.valuation.report"]
        report = model.create(self._prepare_stock_inventory_valuation_report())
        context1["active_id"] = report.id
        context1["active_ids"] = report.ids
        vals["context"] = context1
        return vals

    def button_export_pdf(self):
        self.ensure_one()
        return self._export(report_type="qweb-pdf")

    def button_export_xlsx(self):
        self.ensure_one()
        return self._export(report_type="xlsx")

    def _prepare_stock_inventory_valuation_report(self):
        self.ensure_one()
        return {
            "company_id": self.env.user.company_id.id,
            "compute_at_date": int(self.compute_at_date),
            "date": self.inventory_datetime,
        }

    def _export(self, report_type):
        model = self.env["report.stock.inventory.valuation.report"]
        report = model.create(self._prepare_stock_inventory_valuation_report())
        return report.print_report(report_type)
