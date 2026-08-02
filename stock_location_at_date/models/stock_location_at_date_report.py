import logging

from odoo import fields, models, tools

_logger = logging.getLogger(__name__)


class StockLocationAtDateReport(models.Model):
    _name = "stock.location.at.date.report"
    _description = "Location-Wise Inventory At Date"
    _auto = False
    _order = "location_id, product_id"

    create_uid = fields.Many2one("res.users", string="Created By", readonly=True)
    at_date = fields.Date(string="Stock As Of Date", readonly=True)
    location_id = fields.Many2one("stock.location", string="Location", readonly=True)
    location_complete_name = fields.Char(string="Location Path", readonly=True)
    location_usage = fields.Selection(
        selection=[
            ("supplier", "Vendor Location"),
            ("view", "View"),
            ("internal", "Internal Location"),
            ("customer", "Customer Location"),
            ("inventory", "Inventory Loss"),
            ("production", "Production"),
            ("transit", "Transit Location"),
        ],
        string="Location Type",
        readonly=True,
    )

    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    product_tmpl_id = fields.Many2one(
        "product.template", string="Product Template", readonly=True
    )
    categ_id = fields.Many2one(
        "product.category", string="Product Category", readonly=True
    )
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", readonly=True)

    lot_id = fields.Many2one("stock.lot", string="Lot / Serial No.", readonly=True)
    package_id = fields.Many2one("stock.quant.package", string="Package", readonly=True)

    quantity = fields.Float(digits="Product Unit of Measure", readonly=True)
    unit_cost = fields.Monetary(currency_field="currency_id", readonly=True)
    total_value = fields.Monetary(currency_field="currency_id", readonly=True)

    company_id = fields.Many2one("res.company", readonly=True)
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", readonly=True
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE UNLOGGED TABLE IF NOT EXISTS {self._table} (
                id SERIAL PRIMARY KEY,
                create_uid INTEGER,
                create_date TIMESTAMP,
                at_date DATE,
                company_id INTEGER,
                location_id INTEGER,
                location_complete_name VARCHAR,
                location_usage VARCHAR,
                product_id INTEGER,
                product_tmpl_id INTEGER,
                categ_id INTEGER,
                uom_id INTEGER,
                lot_id INTEGER,
                package_id INTEGER,
                quantity NUMERIC,
                unit_cost NUMERIC,
                total_value NUMERIC
            )
            """
        )
        self.env.cr.execute(
            f"""
            CREATE INDEX IF NOT EXISTS stock_location_at_date_report_uid_idx
            ON {self._table} (create_uid)
            """
        )
