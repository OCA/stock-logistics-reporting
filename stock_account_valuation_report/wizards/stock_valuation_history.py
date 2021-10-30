# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# Copyright 2019 Aleph Objects, Inc.
from odoo import fields, models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


class StockValuationHistory(models.TransientModel):
    _name = "stock.valuation.history"
    _description = "Stock Valuation History"

    inventory_datetime = fields.Datetime(
        "Dual Valuation at Date",
        help="Choose a date to get the valuation at that date",
        default=fields.Datetime.now,
    )

    def open_at_date(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock_account_valuation_report.product_valuation_action"
        )
        domain = [("type", "=", "product")]
        product_id = self.env.context.get("product_id", False)
        product_tmpl_id = self.env.context.get("product_tmpl_id", False)
        if product_id:
            domain = expression.AND([domain, [("id", "=", product_id)]])
        elif product_tmpl_id:
            domain = expression.AND(
                [domain, [("product_tmpl_id", "=", product_tmpl_id)]]
            )
        action["domain"] = domain
        if self.inventory_datetime:
            action_context = safe_eval(action["context"])
            action_context["at_date"] = self.inventory_datetime
            action["context"] = action_context
        return action
