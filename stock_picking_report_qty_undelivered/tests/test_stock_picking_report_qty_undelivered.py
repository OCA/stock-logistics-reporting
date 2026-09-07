# Copyright 2024 Moduon Team S.L.
# License GPL-3.0 (https://www.gnu.org/licenses/gpl-3.0)


from odoo.addons.base.tests.common import BaseCommon


class TestReportQtyUndelivered(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product1 = cls.env["product.product"].create(
            {"name": "Product Test 1", "type": "consu", "is_storable": True}
        )
        cls.product2 = cls.env["product.product"].create(
            {
                "name": "Product Test 2",
                "type": "consu",
                "is_storable": True,
            }
        )
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")

    def _create_done_picking_without_backorder(self):
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.stock_location, 10
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product2, self.stock_location, 10
        )
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": self.picking_type_out.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product1.id,
                            "product_uom": self.product1.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                            "product_uom_qty": 10,
                            "quantity": 4,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product2.id,
                            "product_uom": self.product1.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                            "product_uom_qty": 10,
                            "quantity": 10,
                        },
                    ),
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.filtered(
            lambda move: move.product_id == self.product1
        ).quantity = 4
        picking.with_context(
            skip_backorder=True, picking_ids_not_to_backorder=picking.ids
        ).button_validate()
        return picking

    def _render_delivery_html(self, picking):
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html(
            "stock.action_report_delivery", picking.ids
        )
        return html.decode() if isinstance(html, bytes) else html

    def test_report_qty_not_delivered(self):
        """Test delivery"""
        picking = self._create_done_picking_without_backorder()
        report_html = self._render_delivery_html(picking)
        self.assertNotIn("Summary of undelivered quantities:", report_html)
        self.picking_type_out.summary_qty_undelivered = True
        report_html = self._render_delivery_html(picking)
        summary_html = report_html.split("Summary of undelivered quantities:")[1]
        self.assertIn("Summary of undelivered quantities:", report_html)
        self.assertIn("Product Test 1", summary_html)
        self.assertNotIn("Product Test 2", summary_html)

    def test_report_qty_not_delivered_pdf_smoke(self):
        picking = self._create_done_picking_without_backorder()
        self.picking_type_out.summary_qty_undelivered = True
        wkhtmltopdf_state = self.env["ir.actions.report"].get_wkhtmltopdf_state()
        if wkhtmltopdf_state != "ok":  # pragma: no cover
            self.skipTest(f"wkhtmltopdf is not ready: {wkhtmltopdf_state}")
        with self.allow_pdf_render():
            report_pdf, report_type = (
                self.env["ir.actions.report"]
                .with_context(force_report_rendering=True)
                ._render_qweb_pdf("stock.action_report_delivery", picking.ids)
            )
        self.assertEqual(report_type, "pdf")
        self.assertTrue(report_pdf)

    def test_report_qty_not_delivered_aggregated_ordered_quantity(self):
        picking = self._create_done_picking_without_backorder()
        self.picking_type_out.summary_qty_undelivered = True
        report_html = self._render_delivery_html(picking)
        product_html = report_html.split("Product Test 1")[1].split("Product Test 2")[0]
        self.assertIn(">10<", product_html)
        self.assertIn(">4<", product_html)
        self.assertIn(
            "Summary of undelivered quantities:",
            report_html,
        )
