# Copyright 2020, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import textwrap

from odoo import _, fields, models


class StockKardexReportWiz(models.TransientModel):
    _name = "stock.kardex.report.wiz"
    _description = "Wizard to create kardex reports of stock moves"

    date_from = fields.Datetime(
        string="From", required=True, default=fields.Datetime.now
    )
    date_to = fields.Datetime(string="To", required=True, default=fields.Datetime.now)
    product = fields.Many2one("product.product", required=True, ondelete="cascade")
    location = fields.Many2one("stock.location", required=True, ondelete="cascade")

    def open_table(self):
        self.env["stock.kardex.report"].search([]).unlink()
        self._cr.execute(
            """
        SELECT
        table_one.done - table_two.done
        AS
        total,
        table_one.cost - table_two.cost
        AS
        total_cost
        FROM
        (
            SELECT sum(move_line.qty_done)
            AS
            done,
            sum(move.price_unit * move_line.qty_done)
            AS
            cost
            FROM
            stock_move_line move_line
            INNER JOIN
            stock_move move
            ON move_line.move_id = move.id
            WHERE
            move_line.product_id = %s
            AND
            move_line.state = \'done\'
            AND
            move_line.date < %s
            AND
            move_line.location_dest_id = %s
        )
        table_one
        CROSS JOIN
        (
            SELECT sum(move_line.qty_done)
            AS
            done,
            sum(move.price_unit * move_line.qty_done)
            AS
            cost
            FROM
            stock_move_line move_line
            INNER JOIN
            stock_move move
            ON move_line.move_id = move.id
            WHERE
            move_line.product_id = %s
            AND
            move_line.state = \'done\'
            AND
            move_line.date < %s
            AND
            move_line.location_id = %s
        )
        table_two
        """,
            [
                self.product.id,
                self.date_from,
                self.location.id,
                self.product.id,
                self.date_from,
                self.location.id,
            ],
        )
        start_qty = self._cr.dictfetchall()
        total = start_qty[0]["total"]
        total_cost = start_qty[0]["total_cost"]
        if str(total) == "None":
            total = 0.0
        if str(total_cost) == "None":
            total_cost = 0.0
        self._cr.execute(
            """WITH one AS (
            SELECT
            sml.product_id, sml.product_uom_id,
            sml.lot_id, sml.owner_id, sml.package_id,
            sml.qty_done, sml.move_id, sml.location_id,
            sml.location_dest_id, sm.date, sm.origin,
            sm.state, sm.price_unit
            FROM stock_move_line sml
            INNER JOIN stock_move sm
            ON sml.move_id = sm.id
            WHERE
            sm.date >= %s
            AND sm.date <= %s),
            two AS (
                SELECT *
                FROM one
                WHERE location_id = %s
                OR location_dest_id = %s)
            SELECT *
            FROM two
            WHERE product_id = %s
            AND state = 'done'
            ORDER BY date;""",
            [
                self.date_from,
                self.date_to,
                self.location.id,
                self.location.id,
                self.product.id,
            ],
        )
        moves = self._cr.dictfetchall()
        report_list = []
        report_list.append(
            {
                "product_id": self.product.id,
                "qty_done": 0,
                "date": self.date_from,
                "origin": _("Initial Balance"),
                "balance": total,
                "cost": total_cost,
            }
        )
        for rec in moves:
            if str(rec["price_unit"]) == "None":
                price_unit = 0.0
            else:
                price_unit = rec["price_unit"]
            done_qty = rec["qty_done"]
            if rec["location_id"] == self.location.id:
                done_qty = -rec["qty_done"]
            total += done_qty
            total_cost += (price_unit * done_qty)
            origin = rec["origin"]
            if origin:
                origin = textwrap.shorten(rec["origin"], width=80, placeholder="...")
            line = {
                "move_id": rec["move_id"],
                "product_id": rec["product_id"],
                "product_uom_id": rec["product_uom_id"],
                "lot_id": rec["lot_id"],
                "owner_id": rec["owner_id"],
                "package_id": rec["package_id"],
                "qty_done": done_qty,
                "location_id": rec["location_id"],
                "location_dest_id": rec["location_dest_id"],
                "date": rec["date"],
                "balance": total,
                "origin": origin,
                "cost": total_cost,
            }
            report_list.append(line)
        self.env["stock.kardex.report"].create(report_list)
        tree_view_id = self.env.ref(
            "stock_kardex_report.stock_kardex_report_tree_view"
        ).id
        action = {
            "type": "ir.actions.act_window",
            "views": [(tree_view_id, "tree")],
            "view_id": tree_view_id,
            "view_mode": "tree",
            "name": _("Stock Report"),
            "res_model": "stock.kardex.report",
        }
        return action
