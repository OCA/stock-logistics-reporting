# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockCardView(models.TransientModel):
    _name = "stock.card.view"
    _description = "Stock Card View"
    _order = "date"

    parent_location_id = fields.Many2one(comodel_name="stock.location")
    date = fields.Datetime()
    product_id = fields.Many2one(comodel_name="product.product")
    product_qty = fields.Float()
    product_uom_qty = fields.Float()
    product_uom = fields.Many2one(comodel_name="uom.uom")
    reference = fields.Char()
    location_id = fields.Many2one(comodel_name="stock.location")
    location_dest_id = fields.Many2one(comodel_name="stock.location")
    is_initial = fields.Boolean()
    product_in = fields.Float()
    product_out = fields.Float()
    picking_id = fields.Many2one(comodel_name="stock.picking")

    def name_get(self):
        result = []
        for rec in self:
            name = rec.reference
            if rec.picking_id.sudo().origin:
                name = "{} ({})".format(name, rec.picking_id.sudo().origin)
            result.append((rec.id, name))
        return result


class StockCardReport(models.TransientModel):
    _name = "report.stock.card.report"
    _description = "Stock Card Report"

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    product_ids = fields.Many2many(comodel_name="product.product")
    location_ids = fields.Many2many(comodel_name="stock.location")
    card_types = fields.Selection(
        selection=[
            ("detail", "Detail"),
            ("summary", "Summary"),
        ],
        default="detail",
    )

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="stock.card.view",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def _compute_results(self):
        self.ensure_one()
        date_from = self.date_from or "0001-01-01"
        self.date_to = self.date_to or fields.Date.context_today(self)
        ReportLine = self.env["stock.card.view"]
        stock_card_results = []
        stock_card_lines = []
        for location in self.location_ids:
            locations = self.env["stock.location"].search(
                [("id", "child_of", location.id)]
            )
            self._cr.execute(
                """
                SELECT move.date, move.product_id, move.product_qty,
                    move.product_uom_qty, move.product_uom, move.reference,
                    move.location_id, move.location_dest_id,
                    case when move.location_dest_id in %s
                        then move.product_qty end as product_in,
                    case when move.location_id in %s
                        then move.product_qty end as product_out,
                    case when move.date < %s then True else False end as is_initial,
                    move.picking_id
                FROM stock_move move
                WHERE (move.location_id in %s or move.location_dest_id in %s)
                    and move.state = 'done' and move.product_id in %s
                    and CAST(move.date AS date) <= %s
                ORDER BY move.date, move.reference
            """,
                (
                    tuple(locations.ids),
                    tuple(locations.ids),
                    date_from,
                    tuple(locations.ids),
                    tuple(locations.ids),
                    tuple(self.product_ids.ids),
                    self.date_to,
                ),
            )
            stock_card_results = self._cr.dictfetchall()
            stock_card_lines += [
                ReportLine.new({**line, "parent_location_id": location}).id
                for line in stock_card_results
            ]
        self.results = stock_card_lines

    def _get_initial(self, product_line):
        product_input_qty = sum(product_line.mapped("product_in"))
        product_output_qty = sum(product_line.mapped("product_out"))
        return product_input_qty - product_output_qty

    def _get_product_vals(self, product, location):
        # Initial Vals
        initial_line = self.results.filtered(
            lambda l: l.product_id == product
            and l.is_initial
            and l.parent_location_id == location
        )
        initial_input_qty = sum(initial_line.mapped("product_in"))
        initial_output_qty = sum(initial_line.mapped("product_out"))
        # Product Vals
        product_line = self.results.filtered(
            lambda l: l.product_id == product
            and not l.is_initial
            and l.parent_location_id == location
        )
        product_input_qty = sum(product_line.mapped("product_in"))
        product_output_qty = sum(product_line.mapped("product_out"))
        result = {
            "initial": initial_input_qty - initial_output_qty,
            "balance": product_input_qty - product_output_qty,
            "product_in": product_input_qty,
            "product_out": product_output_qty,
        }
        return result

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        if report_type == "xlsx":
            action = self.env.ref("stock_card_report.action_stock_card_report_xlsx")
        elif report_type == "summary_xlsx":
            action = self.env.ref(
                "stock_card_report.action_stock_card_summary_report_xlsx"
            )
        else:
            action = self.env.ref("stock_card_report.action_stock_card_report_pdf")
        return action.report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        report = self.browse(self._context.get("active_id"))
        if report:
            rcontext["o"] = report
            result["html"] = self.env.ref(
                "stock_card_report.report_stock_card_report_html"
            )._render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(**(given_context or {}))._get_html()
