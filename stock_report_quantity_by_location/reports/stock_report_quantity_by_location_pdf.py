from odoo import api, fields, models


class StockReportQuantityByProductView(models.TransientModel):
    _name = "stock.report.quantity.by.product.view"
    _description = "Stock Report Quantity By Product View"

    report_id = fields.Many2one("report.stock.report.quantity.by.location.pdf")
    name = fields.Char()


class StockReportQuantityByLocationView(models.TransientModel):
    _name = "stock.report.quantity.by.location.view"
    _description = "Stock Report Quantity By Location View"

    report_location_id = fields.Many2one("report.stock.report.quantity.by.location.pdf")

    loc_name = fields.Char()
    product_name = fields.Char()
    quantity_on_hand = fields.Float()
    quantity_reserved = fields.Float()
    quantity_unreserved = fields.Float()


class StockReportQuantityByLocationReport(models.TransientModel):
    _name = "report.stock.report.quantity.by.location.pdf"
    _description = "Stock Report Quantity By Location"

    location_ids = fields.Many2many(
        comodel_name="stock.location", string="Locations", required=True
    )

    with_quantity = fields.Boolean(
        string="Quantity>0",
        default=True,
        help="Show only the products that have existing quantity on hand",
    )

    results = fields.One2many(
        comodel_name="stock.report.quantity.by.product.view",
        inverse_name="report_id",
        compute="_compute_results",
    )

    results_location = fields.One2many(
        comodel_name="stock.report.quantity.by.location.view",
        inverse_name="report_location_id",
        compute="_compute_results",
    )

    @api.depends("location_ids")
    def _compute_results(self):
        """
        Generate report lines
        """
        self.ensure_one()
        results = self.env["stock.report.quantity.by.product.view"]
        results_location = self.env["stock.report.quantity.by.location.view"]
        products = self.env["product.product"].search([("type", "=", "product")])
        for product in products:
            product_exist = False
            for loc in self.location_ids:
                available_products = self.env["stock.quant"].read_group(
                    [
                        ("product_id", "=", product.id),
                        ("location_id", "child_of", [loc.id]),
                    ],
                    ["quantity", "reserved_quantity", "product_id"],
                    ["product_id"],
                )
                if available_products:
                    qty_on_hand = available_products[0]["quantity"]
                    qty_reserved = available_products[0]["reserved_quantity"]
                    qty_unreserved = qty_on_hand - qty_reserved
                    if (not self.with_quantity) or qty_on_hand > 0:
                        product_exist = True
                        vals = {
                            "loc_name": loc.display_name,
                            "product_name": product.display_name,
                            "quantity_on_hand": qty_on_hand,
                            "quantity_reserved": qty_reserved,
                            "quantity_unreserved": qty_unreserved,
                        }
                        results_location |= results_location.new(vals)
            if product_exist:
                vals_product = {
                    "name": product.display_name,
                }
                results |= results.new(vals_product)
        self.results = results
        self.results_location = results_location

    def print_report(self):
        self.ensure_one()
        action = self.env.ref(
            "stock_report_quantity_by_location."
            "action_stock_report_quantity_by_location_pdf",
            raise_if_not_found=False,
        )
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env["ir.qweb"]._render(
                "stock_report_quantity_by_location."
                "report_stock_report_quantity_by_location_html",
                rcontext,
            )
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(**(given_context or {}))._get_html()
