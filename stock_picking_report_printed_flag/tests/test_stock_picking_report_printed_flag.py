from odoo.addons.base.tests.common import BaseCommon


class TestReportPrintedFlagStock(BaseCommon):
    """
    Test suite for stock_picking_report_printed_flag.
    Covers:
    - printed flag behavior
    - log creation
    - printed report names computation
    - multi-record handling
    - non-configured reports
    - UI actions
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        # ---------------------------
        # PICKING TYPE
        # ---------------------------
        cls.picking_type = cls.env.ref("stock.picking_type_out").with_company(
            cls.company
        )
        # ---------------------------
        # LOCATIONS
        # ---------------------------
        cls.location_src = cls.env.ref("stock.stock_location_stock")
        cls.location_dest = cls.env.ref("stock.stock_location_customers")
        # ---------------------------
        # PARTNER
        # ---------------------------
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        # ---------------------------
        # PICKING
        # ---------------------------
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.picking_type.id,
                "location_id": cls.location_src.id,
                "location_dest_id": cls.location_dest.id,
                "company_id": cls.company.id,
            }
        )
        # ---------------------------
        # QWEB TEMPLATE
        # ---------------------------
        cls.env["ir.ui.view"].create(
            {
                "name": "test_stock_report_template",
                "type": "qweb",
                "key": "stock_picking_report_printed_flag.test_template",
                "arch": """
                <t t-name="stock_picking_report_printed_flag.test_template">
                    <t t-foreach="docs" t-as="o">
                        <div>
                            <span t-esc="o.id"/>
                        </div>
                    </t>
                </t>
            """,
            }
        )
        # ---------------------------
        # REPORT
        # ---------------------------
        cls.report = cls.env["ir.actions.report"].create(
            {
                "name": "Test Picking Report",
                "model": "stock.picking",
                "report_type": "qweb-pdf",
                "report_name": "stock_picking_report_printed_flag.test_template",
            }
        )
        # ---------------------------
        # CONFIG
        # ---------------------------
        cls.config = cls.env["report.printed.config"].create(
            {
                "name": "Stock Config",
                "model_id": cls.env["ir.model"]._get("stock.picking").id,
                "company_id": cls.company.id,
                "report_printed_log_active": True,
                "report_printed_names_active": True,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "report_id": cls.report.id,
                        },
                    )
                ],
            }
        )

    # ---------------------------
    # TESTS
    # ---------------------------
    def test_printed_flag(self):
        """Printing should mark picking as printed"""
        self.assertFalse(self.picking.printed)
        self.report._render_qweb_pdf(
            self.report.report_name,
            self.picking.ids,
        )
        self.picking.invalidate_recordset()
        self.assertTrue(self.picking.printed)

    def test_log_created(self):
        """Printing should create a log entry"""
        self.env["report.printed.log"].search([]).unlink()
        self.report._render_qweb_pdf(
            self.report.report_name,
            self.picking.ids,
        )
        logs = self.env["report.printed.log"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
            ]
        )
        self.assertTrue(logs)

    def test_printed_report_names(self):
        """Printed report names should be computed"""
        self.report._render_qweb_pdf(
            self.report.report_name,
            self.picking.ids,
        )
        self.picking.invalidate_recordset()
        self.assertTrue(self.picking.printed_report_names)
        self.assertIn("Test Picking Report", self.picking.printed_report_names)

    def test_multiple_records(self):
        """Batch printing should mark all pickings"""
        picking2 = self.picking.copy()
        self.report._render_qweb_pdf(
            self.report.report_name,
            (self.picking | picking2).ids,
        )
        self.picking.invalidate_recordset()
        picking2.invalidate_recordset()
        self.assertTrue(self.picking.printed)
        self.assertTrue(picking2.printed)

    def test_multiple_logs(self):
        """Multiple prints should create multiple logs"""
        self.env["report.printed.log"].search([]).unlink()
        self.report._render_qweb_pdf(
            self.report.report_name,
            self.picking.ids,
        )
        self.report._render_qweb_pdf(
            self.report.report_name,
            self.picking.ids,
        )
        logs = self.env["report.printed.log"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
            ]
        )
        self.assertEqual(
            len(logs),
            2,
            "Each report execution should create a separate log entry.",
        )

    def test_report_not_configured(self):
        """Non-configured report should not mark printed or create logs."""
        other_report = self.env["ir.actions.report"].create(
            {
                "name": "Other Report",
                "model": "stock.picking",
                "report_type": "qweb-pdf",
                "report_name": ("stock_picking_report_printed_flag.test_template"),
            }
        )
        self.env["report.printed.log"].search([]).unlink()
        self.picking.write({"printed": False})
        other_report._render_qweb_pdf(
            other_report.report_name,
            self.picking.ids,
        )
        self.picking.invalidate_recordset()
        logs = self.env["report.printed.log"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
            ]
        )
        self.assertFalse(self.picking.printed)
        self.assertFalse(logs)

    def test_action_view_printed_logs(self):
        """UI action should return correct domain."""
        action = self.picking.action_view_printed_logs()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "report.printed.log")
        self.assertEqual(action["view_mode"], "tree")
        self.assertIn(
            ("res_model", "=", "stock.picking"),
            action["domain"],
        )
        self.assertIn(
            ("res_id", "=", self.picking.id),
            action["domain"],
        )

    def test_stock_picking_has_printed_mixin_fields(self):
        """Stock pickings should expose fields provided by the printed mixin."""
        self.assertIn("printed", self.picking._fields)
        self.assertIn("printed_log_ids", self.picking._fields)
        self.assertIn("printed_report_names", self.picking._fields)

    def test_log_values(self):
        """Printed log should contain stock picking metadata."""
        self.env["report.printed.log"].search([]).unlink()
        self.report._render_qweb_pdf(
            self.report.report_name,
            self.picking.ids,
        )
        log = self.env["report.printed.log"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
            ],
            limit=1,
        )
        self.assertTrue(log)
        self.assertEqual(log.res_model, "stock.picking")
        self.assertEqual(log.res_id, self.picking.id)
        self.assertEqual(log.report_id, self.report)
        self.assertEqual(log.company_id, self.company)
        self.assertEqual(log.user_id, self.env.user)

    def test_logs_disabled(self):
        """Logs should not be created when disabled in configuration."""
        self.config.write(
            {
                "report_printed_log_active": False,
                "report_printed_names_active": False,
            }
        )
        self.env["report.printed.log"].search([]).unlink()
        self.report._render_qweb_pdf(
            self.report.report_name,
            self.picking.ids,
        )
        logs = self.env["report.printed.log"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
            ]
        )
        self.assertFalse(logs)
