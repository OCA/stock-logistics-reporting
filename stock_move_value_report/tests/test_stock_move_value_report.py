# Copyright 2025 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.addons.stock_account.tests.common import TestStockValuationCommon


class Test(TestStockValuationCommon):
    """
    Tests for stock_move_value_report.
    """

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
        self.env["ir.actions.report"].with_context(**context)._render_qweb_pdf(
            report_name, records.ids, data={"context": context}
        )

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
        self._render_report(report_name, move.picking_id)

    def test_report_stock_scrap_value(self):
        report_name = "stock_move_value_report.report_stock_scrap_value"
        scrap = self.env["stock.scrap"].create(
            {
                "product_id": self.product_standard.id,
                "product_uom_id": self.product_standard.uom_id.id,
            }
        )
        self._render_report(report_name, scrap)
