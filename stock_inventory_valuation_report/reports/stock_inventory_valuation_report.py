# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class StockInventoryValuationView(models.TransientModel):
    _name = "stock.inventory.valuation.view"
    _description = "Stock Inventory Valuation View"

    report_id = fields.Many2one("report.stock.inventory.valuation.report")

    name = fields.Char()
    reference = fields.Char()
    barcode = fields.Char()
    qty_at_date = fields.Float()
    uom_id = fields.Many2one(
        comodel_name="uom.uom",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
    )
    cost_currency_id = fields.Many2one(
        comodel_name="res.currency",
    )
    standard_price = fields.Float()
    stock_value = fields.Float()
    cost_method = fields.Char()


class StockInventoryValuationReport(models.TransientModel):
    _name = "report.stock.inventory.valuation.report"
    _description = "Stock Inventory Valuation Report"

    # Filters fields, used for data computation
    company_id = fields.Many2one(
        comodel_name="res.company",
    )
    inventory_datetime = fields.Datetime(required=True, default=fields.Datetime.now)

    results = fields.One2many(
        comodel_name="stock.inventory.valuation.view",
        inverse_name="report_id",
        compute="_compute_results",
    )

    @api.depends("inventory_datetime")
    def _compute_results(self):
        """
        Generate report lines, one per product present at the time
        """
        self.ensure_one()
        domain = [("type", "=", "product")]
        product_id = self.env.context.get("product_id")
        product_tmpl_id = self.env.context.get("product_tmpl_id")
        if product_id:
            domain = expression.AND([domain, [("id", "=", product_id)]])
        elif product_tmpl_id:
            domain = expression.AND(
                [domain, [("product_tmpl_id", "=", product_tmpl_id)]]
            )
        products = (
            self.env["product.product"]
            .with_context(
                to_date=self.inventory_datetime,
                company_owned=True,
                create=False,
                edit=False,
            )
            .search(domain)
            # 'quantity_svl' is not stored, can't be used in search
        ).filtered(lambda pp: pp.quantity_svl != 0)
        results = self.env["stock.inventory.valuation.view"]
        if products:
            for product in products:
                vals = {
                    "name": product.with_context(
                        display_default_code=False
                    ).display_name,
                    "reference": product.default_code,
                    "barcode": product.barcode,
                    "qty_at_date": product.quantity_svl,
                    "uom_id": product.uom_id,
                    "currency_id": product.currency_id,
                    "cost_currency_id": product.cost_currency_id,
                    "standard_price": product.standard_price,
                    "stock_value": product.value_svl,
                    "cost_method": product.cost_method,
                }
                results |= results.new(vals)
        self.results = results

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env.ref(
                "stock_inventory_valuation_report."
                "action_stock_inventory_valuation_report_xlsx",
                raise_if_not_found=False,
            )
            or self.env.ref(
                "stock_inventory_valuation_report."
                "action_stock_inventory_valuation_report_pdf",
                raise_if_not_found=False,
            )
        )
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "stock_inventory_valuation_report."
                "report_stock_inventory_valuation_report_html"
            )._render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()
