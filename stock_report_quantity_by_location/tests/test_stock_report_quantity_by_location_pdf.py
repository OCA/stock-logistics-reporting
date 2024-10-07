from odoo.tests.common import TransactionCase
from odoo.tools import test_reports


class TestStockReportQuantityByLocationPdf(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.stock_report_qty_by_loc_pdf_model = cls.env[
            "report.stock.report.quantity.by.location.pdf"
        ]

        cls.qweb_report_name = (
            "stock_report_quantity_by_location."
            "report_stock_report_quantity_by_location_pdf"
        )

        cls.report_title = "Stock Report Quantity By Location"

        cls.base_filters = {
            "with_quantity": True,
        }

        cls.report = cls.stock_report_qty_by_loc_pdf_model.create(cls.base_filters)

    def test_html(self):
        test_reports.try_report(
            self.env.cr,
            self.env.uid,
            self.qweb_report_name,
            [self.report.id],
            report_type="qweb-html",
        )

    def test_qweb(self):
        test_reports.try_report(
            self.env.cr,
            self.env.uid,
            self.qweb_report_name,
            [self.report.id],
            report_type="qweb-pdf",
        )

    def test_print(self):
        self.report.print_report()
