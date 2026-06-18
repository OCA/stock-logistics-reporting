# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools
from odoo.tools import SQL


class StockMoveDelayReport(models.Model):
    _name = "stock.move.delay.report"
    _description = "Delay Analysis Report"
    _auto = False

    date = fields.Date("Done Date", readonly=True)
    create_date = fields.Date("Created Date", readonly=True)
    original_date = fields.Date("Scheduled Date", readonly=True)
    move_id = fields.Many2one("stock.move", "Stock Move #", readonly=True)
    product_id = fields.Many2one("product.product", "Product", readonly=True)
    reference = fields.Char(readonly=True)
    location_src_id = fields.Many2one("stock.location", "From", readonly=True)
    location_dest_id = fields.Many2one("stock.location", "To", readonly=True)
    date_delay = fields.Float(aggregator="avg", readonly=True)
    delivery_time = fields.Float(aggregator="avg", readonly=True)
    done_on_time = fields.Float("Done on Time", aggregator="avg", readonly=True)
    product_uom = fields.Many2one("uom.uom", "Unit of Measure", readonly=True)
    supplier_id = fields.Many2one("res.partner", "Supplier", readonly=True)
    company_id = fields.Many2one("res.company", string="Company")

    def _done_on_time(self):
        return """
            case when sm.date_delay > 0 then 0.0 else 100.0 end as done_on_time
        """

    def _select(self):
        return f"""
            sm.id,
            COALESCE(sm.original_date, picking.scheduled_date) AS original_date,
            sm.create_date,
            sm.date,
            sm.id AS move_id,
            sm.product_id,
            sm.reference,
            sm.location_id AS location_src_id,
            sm.location_dest_id,
            sm.date_delay,
            sm.delivery_time,
            {self._done_on_time()},
            sm.product_uom,
            sm.supplier_id,
            sm.company_id
        """

    def _from(self):
        return """
            stock_move AS sm
            LEFT JOIN stock_picking picking ON sm.picking_id = picking.id
        """

    def _where(self):
        return """
            sm.state = 'done' AND sm.supplier_id IS NOT NULL
        """

    def _query(self):
        return f"""
            (SELECT {self._select()}
            FROM {self._from()}
            WHERE {self._where()})
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = self._query()
        self.env.cr.execute(
            SQL(
                """
                CREATE or REPLACE VIEW %s as (%s)
                """,
                SQL.identifier(self._table),
                SQL(query),
            )
        )
