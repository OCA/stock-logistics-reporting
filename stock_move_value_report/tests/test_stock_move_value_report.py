# Copyright 2025 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.addons.stock_account.tests.common import TestStockValuationCommon


class Test(TestStockValuationCommon):
    """
    Tests for stock_move_value_report.
    """

    _test_user_groups = (
        "stock.group_stock_manager",
        "account.group_account_manager",
        "stock.group_production_lot",
    )

    def _make_move(self):
        return self._make_in_move(
            self.product_standard, 10, unit_cost=15, create_picking=True
        )

    def _render_report(self, report_name, records):
        """
        Ensure rendering passes without errors
        """
        context = {
            **self.env.context,
            "active_ids": records.ids,
            "active_model": "stock.move",
        }
        report = self.env["ir.actions.report"].with_context(**context)
        html = report._render_qweb_html(
            report_name, records.ids, data={"context": context}
        )[0]
        report._render_qweb_pdf(report_name, records.ids, data={"context": context})
        return html if isinstance(html, str) else html.decode("utf-8")

    def test_report_stock_move_line_value(self):
        report_name = "stock_move_value_report.report_stock_move_line_value"
        move = self._make_move()
        self._render_report(report_name, move.move_line_ids)

    def test_report_stock_move_value(self):
        report_name = "stock_move_value_report.report_stock_move_value"
        move = self._make_move()
        self._render_report(report_name, move)

    def test_report_stock_picking_value(self):
        report_name = "stock_move_value_report.report_stock_picking_value"
        move = self._make_move()
        html = self._render_report(report_name, move.picking_id)
        self.assertIn("150.00", html)
        self.assertIn(move.picking_id.location_id.name, html)
        self.assertIn(move.picking_id.location_dest_id.name, html)

    def test_report_stock_scrap_value(self):
        report_name = "stock_move_value_report.report_stock_scrap_value"
        self._make_move()
        scrap = self.env["stock.move"].create(
            {
                "is_scrap": True,
                "product_id": self.product_standard.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.company.scrap_location_id.id,
                "quantity": 1,
                "company_id": self.env.company.id,
            }
        )
        scrap.action_scrap()
        self._render_report(report_name, scrap)
        self._render_report("stock_move_value_report.report_stock_move_value", scrap)
        self._render_report(
            "stock_move_value_report.report_stock_move_line_value",
            scrap.move_line_ids,
        )
