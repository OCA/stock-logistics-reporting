# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class StockReportQuantityLocationDate(models.TransientModel):

    _name = "stock.report.quantity.location.date"
    _description = "Stock Quantity Report by Location and Date"

    location_ids = fields.Many2many(
        comodel_name="stock.location",
    )
    pivot_date = fields.Date(
        required=True,
        default=lambda self: fields.Date.today(),
        help="Fill in this in order to get the inventory value at that date.",
    )

    def _add_stock_data_query(self, report_query):
        location_ids = self.location_ids.ids
        if not location_ids:
            location_ids = (
                self.env["stock.location"].search([("usage", "=", "internal")]).ids
            )
        location_str = ",".join([str(loc_id) for loc_id in location_ids])
        added_query = """
            SELECT
                sm.date,
                sm.product_id,
                sm.location_id as location,
                sum(sm.product_uom_qty) * -1 as qty
            FROM stock_move sm
            WHERE location_id in ({location1})
                AND state='done'
                AND date <= '{pivot_date}'
            GROUP BY
                sm.date,
                sm.product_id,
                sm.location_id
            UNION ALL
            SELECT
                sm.date,
                sm.product_id,
                sm.location_dest_id as location,
                sum(sm.product_uom_qty) as qty
            FROM stock_move sm
            WHERE location_dest_id in ({location2})
                AND state='done'
                AND date <= '{pivot_date}'
            GROUP BY sm.date, sm.product_id, sm.location_dest_id
        """.format(
            location1=location_str,
            location2=location_str,
            pivot_date=fields.Date.to_string(self.pivot_date),
        )
        return "{}{}".format(report_query, added_query)

    def _get_query(self):
        report_query = ""
        report_query = self._add_stock_data_query(report_query)
        return report_query

    def _compute_stock_report_by_location_by_date(self):
        query = self._get_query()

        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()

        vals_list = []
        for result in results:
            vals_list.append(
                {
                    "move_date": result["date"],
                    "product_id": result["product_id"],
                    "location_id": result["location"],
                    "quantity": result["qty"],
                    "wizard_id": self.id,
                }
            )
        recs = self.env["report.stock.quantity.location.date"].create(vals_list)
        return recs

    def doit(self):
        self._compute_stock_report_by_location_by_date()
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "pivot,tree",
            "name": _("Stock Report by Location By Date"),
            "context": {
                "group_by": [],
            },
            "res_model": "report.stock.quantity.location.date",
            "domain": [("wizard_id", "=", self.id)],
        }
        return action
