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
        Generate report lines, one per product with stock at the given date.

        For databases migrated from Odoo 12 to 18 where products changed from
        type='product' to type='consu' + is_storable=True, we need to calculate
        historical quantities from stock.move.line instead of stock_valuation_layer
        because SVL.sum(quantity) gives accumulated historical total, not actual stock.
        """
        self.ensure_one()

        # Build domain for products
        domain = [("is_storable", "=", True)]
        product_id = self.env.context.get("product_id")
        product_tmpl_id = self.env.context.get("product_tmpl_id")
        if product_id:
            domain = expression.AND([domain, [("id", "=", product_id)]])
        elif product_tmpl_id:
            domain = expression.AND(
                [domain, [("product_tmpl_id", "=", product_tmpl_id)]]
            )

        products = self.env["product.product"].search(domain)

        if not products:
            self.results = self.env["stock.inventory.valuation.view"]
            return

        # Flush pending changes to database before SQL query
        self.env.flush_all()

        # Query historical quantities from stock.move.line
        # This gives accurate results for migrated databases
        # Note: We use m.date instead of ml.date because tests may modify
        # move dates after validation
        query = """
            SELECT ml.product_id,
                   COALESCE(
                       SUM(CASE WHEN loc_dest.usage = 'internal'
                           THEN ml.quantity ELSE 0 END), 0
                   ) as qty_in,
                   COALESCE(
                       SUM(CASE WHEN loc_src.usage = 'internal'
                           THEN ml.quantity ELSE 0 END), 0
                   ) as qty_out
            FROM stock_move_line ml
            INNER JOIN stock_location loc_src ON ml.location_id = loc_src.id
            INNER JOIN stock_location loc_dest
                ON ml.location_dest_id = loc_dest.id
            INNER JOIN stock_move m ON ml.move_id = m.id
            WHERE ml.product_id IN %s
              AND ml.state = 'done'
              AND m.date <= %s
              AND m.company_id = %s
            GROUP BY ml.product_id
        """

        self.env.cr.execute(
            query, (tuple(products.ids), self.inventory_datetime, self.env.company.id)
        )

        qty_data = {
            row[0]: row[1] - row[2]  # qty_in - qty_out
            for row in self.env.cr.fetchall()
        }

        # Generate result lines
        results = self.env["stock.inventory.valuation.view"]
        products_with_stock = products.filtered(
            lambda p: p.id in qty_data and qty_data[p.id] > 0
        )

        # Apply context to get historical SVL values
        products_at_date = products_with_stock.with_context(
            to_date=self.inventory_datetime,
            company_owned=True,
        )

        for product, product_at_date in zip(
            products_with_stock, products_at_date, strict=False
        ):
            qty_at_date = qty_data[product.id]

            # Calculate historical cost from SVL (same as Odoo 12 get_history_price)
            # Use value_svl / quantity_svl from product with to_date context
            if product_at_date.quantity_svl:
                standard_price = (
                    product_at_date.value_svl / product_at_date.quantity_svl
                )
            else:
                standard_price = product_at_date.standard_price

            stock_value = qty_at_date * standard_price

            vals = {
                "name": product.with_context(display_default_code=False).display_name,
                "reference": product.default_code,
                "barcode": product.barcode,
                "qty_at_date": qty_at_date,
                "uom_id": product.uom_id.id,
                "currency_id": product.currency_id.id,
                "cost_currency_id": product.cost_currency_id.id,
                "standard_price": standard_price,
                "stock_value": stock_value,
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
            result["html"] = self.env["ir.ui.view"]._render_template(
                "stock_inventory_valuation_report."
                "report_stock_inventory_valuation_report_html",
                values=rcontext,
            )
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(**given_context)._get_html()
