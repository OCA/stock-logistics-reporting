# Copyright 2021 ForgeFlow S.L.
from odoo import fields, models
from odoo.tools.misc import format_date


class WizardStockDiscrepancyReport(models.TransientModel):

    _name = "wizard.stock.discrepancy.report"
    _description = "Stock Discrepancy Report"

    to_date = fields.Datetime(
        string="To date",
        required=True,
        default=fields.Datetime.now(),
    )

    def action_show_discrepancy_report(self):
        product_model = self.env["product.product"]
        product_discrepancy_model = self.env["product.discrepancy"]
        products = product_model.with_context(
            to_date=self.to_date, target_move="posted"
        ).search([("valuation_discrepancy", "!=", 0.0)])
        discrepancy_records = product_discrepancy_model.browse()
        for product in products.read(
            [
                "categ_id",
                "stock_value",
                "account_value",
                "qty_at_date",
                "account_qty_at_date",
                "valuation_discrepancy",
                "qty_discrepancy",
            ],
            load="_classic_write",
        ):
            discrepancy_records |= product_discrepancy_model.create(
                {
                    "product_id": product["id"],
                    "categ_id": product["categ_id"],
                    "stock_value": product["stock_value"],
                    "account_value": product["account_value"],
                    "qty_at_date": product["qty_at_date"],
                    "account_qty_at_date": product["account_qty_at_date"],
                    "valuation_discrepancy": product["valuation_discrepancy"],
                    "qty_discrepancy": product["qty_discrepancy"],
                    "to_date_valuation": self.to_date,
                }
            )
        action = self.env.ref(
            "stock_account_valuation_discrepancy_adjust." "product_discrepancy_action"
        ).read()[0]
        action["domain"] = [("id", "in", discrepancy_records.ids)]
        action["display_name"] = "%s (%s)" % (
            action["display_name"],
            format_date(
                self.env,
                fields.Datetime.context_timestamp(self.env.user, self.to_date),
            ),
        )
        return action
