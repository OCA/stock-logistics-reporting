# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import io

import xlrd

from odoo.tests import Form, HttpCase, tagged


@tagged("-at_install", "post_install")
class TestPortalPickingXlsx(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, mail_notrack=True))
        cls.test_user = cls.env["res.users"].create(
            {"name": "Test User", "login": "test_user", "password": "12345"}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product with lot",
                "is_storable": True,
                "tracking": "lot",
                "list_price": 50.0,
            }
        )
        cls.product_no_lot = cls.env["product.product"].create(
            {
                "name": "Product without lot",
                "is_storable": True,
                "tracking": "none",
                "list_price": 30.0,
            }
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "LOT001",
                "product_id": cls.product.id,
            }
        )
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.test_user.partner_id
        with sale_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 2
        with sale_form.order_line.new() as line:
            line.product_id = cls.product_no_lot
            line.product_uom_qty = 1
        cls.sale_order = sale_form.save()
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids[:1]
        for move in cls.picking.move_ids:
            move.quantity = move.product_uom_qty
        tracked_line = cls.picking.move_line_ids.filtered(
            lambda line: line.product_id.tracking != "none"
        )
        tracked_line.lot_id = cls.lot.id
        cls.picking.button_validate()

    def test_portal_download_xlsx_file(self):
        # Ensure that the Excel file can be downloaded from the portal
        self.authenticate("test_user", "12345")
        url = f"/my/picking/xlsx/{self.picking.id}"
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            response.headers.get("Content-Type", ""),
        )
        self.assertTrue(response.content)
        excel_file = io.BytesIO(response.content)
        book = xlrd.open_workbook(file_contents=excel_file.read())
        sheet = book.sheet_by_index(0)
        # Verify headers and content data
        self.assertEqual(sheet.cell_value(2, 0), "Product")
        self.assertEqual(sheet.cell_value(2, 1), "Lot/Serial Number")
        self.assertEqual(sheet.cell_value(2, 2), "Quantity")
        self.assertEqual(sheet.nrows, 4)
        self.assertEqual(sheet.cell_value(3, 0), self.product.display_name)
        self.assertEqual(sheet.cell_value(3, 1), self.lot.name)
        self.assertEqual(sheet.cell_value(3, 2), 2.0)
        all_product_names = [
            sheet.cell_value(rowx, 0) for rowx in range(3, sheet.nrows)
        ]
        self.assertNotIn(self.product_no_lot.display_name, all_product_names)
