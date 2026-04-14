from odoo.addons.base.tests.common import BaseCommon


class TestStockReportPartnerRef(BaseCommon):
    """
    Test suite for stock_report_partner_ref.
    This test validates that:
    - Reports render correctly without crashing
    - Partner reference (partner.ref) is correctly displayed
    - The logic works both with and without a sale order
    - The system behaves safely when no reference is defined
    Important:
    The picking is generated through a real business flow (sale.order),
    ensuring consistency with how Odoo links sale -> picking -> moves.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        # ---------------------------------------------------------
        # PARTNER (WITH REFERENCE)
        # ---------------------------------------------------------
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "ref": "CUST-001",
            }
        )
        # ---------------------------------------------------------
        # PRODUCT (REQUIRED FOR SALE FLOW)
        # ---------------------------------------------------------
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
            }
        )
        # ---------------------------------------------------------
        # SALE ORDER (REAL FLOW)
        # ---------------------------------------------------------
        cls.sale = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
            }
        )
        cls.sale_line = cls.env["sale.order.line"].create(
            {
                "order_id": cls.sale.id,
                "product_id": cls.product.id,
                "product_uom_qty": 1,
            }
        )
        # Confirm sale to generate picking
        cls.sale.action_confirm()
        # Picking generated from sale
        cls.picking = cls.sale.picking_ids[0]

    # ---------------------------------------------------------
    # TESTS
    # ---------------------------------------------------------
    def test_delivery_report_contains_partner_ref(self):
        """
        Delivery slip report should include partner reference.
        This validates:
        - QWeb inheritance is correctly applied
        - Reference is correctly resolved from sale/picking
        """
        report = self.env.ref("stock.action_report_delivery")
        html, _ = report._render_qweb_html(
            report.report_name,
            self.picking.ids,
        )
        html = html.decode()
        self.assertIn("CUST-001", html)

    def test_picking_report_contains_partner_ref(self):
        """
        Picking operations report should include partner reference.
        Ensures consistency across multiple stock reports.
        """
        report = self.env.ref("stock.action_report_picking")
        html, _ = report._render_qweb_html(
            report.report_name,
            self.picking.ids,
        )
        html = html.decode()
        self.assertIn("CUST-001", html)

    def test_report_without_partner_ref(self):
        """
        Report should render correctly when partner has no reference.
        This validates:
        - Safe fallback logic
        - No crash in QWeb rendering
        """
        partner = self.env["res.partner"].create(
            {
                "name": "No Ref Partner",
            }
        )
        # Create sale flow without ref
        sale = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "order_id": sale.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
            }
        )
        sale.action_confirm()
        picking = sale.picking_ids[0]
        report = self.env.ref("stock.action_report_delivery")
        html, _ = report._render_qweb_html(
            report.report_name,
            picking.ids,
        )
        # Should render without crashing
        self.assertTrue(html)

    def test_partner_ref_fallback_to_commercial(self):
        """
        If contact has no ref, fallback to commercial partner ref.
        """
        parent = self.env["res.partner"].create(
            {
                "name": "Parent Company",
                "ref": "PARENT-REF",
            }
        )
        child = self.env["res.partner"].create(
            {
                "name": "Child Contact",
                "parent_id": parent.id,
            }
        )
        sale = self.env["sale.order"].create(
            {
                "partner_id": child.id,
            }
        )
        self.env["sale.order.line"].create(
            {
                "order_id": sale.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
            }
        )
        sale.action_confirm()
        picking = sale.picking_ids[0]
        report = self.env.ref("stock.action_report_delivery")
        html, _ = report._render_qweb_html(
            report.report_name,
            picking.ids,
        )
        html = html.decode()
        self.assertIn("PARENT-REF", html)
