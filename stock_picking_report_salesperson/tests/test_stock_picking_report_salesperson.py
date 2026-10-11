# Copyright 2026 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from unittest.mock import patch

from odoo.tests.common import TransactionCase, new_test_user
from odoo.tools import html2plaintext


class TestStockPickingReportSalesperson(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.salesperson = new_test_user(
            cls.env,
            login="stock_report_salesperson",
            groups="sales_team.group_sale_salesman",
            name="Stock Report Salesperson",
        )
        cls.stock_user = new_test_user(
            cls.env,
            login="stock_report_user",
            groups="stock.group_stock_user",
            name="Stock Report User",
        )
        cls.partner = cls.env["res.partner"].create({"name": "Report Partner"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Report Product",
                "type": "consu",
                "is_storable": True,
                "list_price": 10.0,
            }
        )

    def _create_outgoing_picking(self, user=False):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": user.id if user else False,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )
        order.action_confirm()
        return order.picking_ids.filtered(
            lambda picking: picking.picking_type_id.code == "outgoing"
        )[:1]

    def _render_report_text(self, report_xmlid, picking):
        report_model = self.env["ir.actions.report"].with_user(self.stock_user)
        with patch.object(type(report_model), "barcode", return_value=b""):
            html = report_model._render_qweb_html(report_xmlid, picking.ids)[0]
        return html2plaintext(html)

    def test_salesperson_is_shown_on_outgoing_picking_reports(self):
        picking = self._create_outgoing_picking(user=self.salesperson)

        for report_xmlid in ("stock.report_deliveryslip", "stock.report_picking"):
            text = self._render_report_text(report_xmlid, picking)
            self.assertIn("Salesperson:", text)
            self.assertIn(self.salesperson.name, text)

    def test_salesperson_is_hidden_without_sale_salesperson(self):
        picking = self._create_outgoing_picking()

        for report_xmlid in ("stock.report_deliveryslip", "stock.report_picking"):
            text = self._render_report_text(report_xmlid, picking)
            self.assertNotIn("Salesperson:", text)
