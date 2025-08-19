import io

import xlsxwriter

from odoo import exceptions
from odoo.http import content_disposition, request, route

from odoo.addons.sale.controllers.portal import CustomerPortal


class StockPortalLotList(CustomerPortal):
    @route(
        ["/my/picking/xlsx/<int:picking_id>"], type="http", auth="public", website=True
    )
    def portal_my_picking_report_xls(self, picking_id, access_token=None, **kw):
        """Download Excel file for picking if user has access"""
        try:
            picking = self._stock_picking_check_access(
                picking_id, access_token=access_token
            )
        except exceptions.AccessError:
            return request.redirect("/my")
        xlsx_content = self._generate_picking_lot_xlsx(picking)
        filename = f"{picking.name}_lots.xlsx"
        return request.make_response(
            xlsx_content,
            headers=[
                (
                    "Content-Type",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
                ("Content-Disposition", content_disposition(filename)),
            ],
        )

    def _generate_picking_lot_xlsx(self, picking):
        """Generate XLSX file for lots in a picking"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Lots")
        # Style
        title_format = workbook.add_format({"bold": True, "font_size": 14})
        header_format = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#DDEEFF",
                "text_wrap": True,
                "valign": "vcenter",
                "align": "center",
                "border": 1,
            }
        )
        cell_format = workbook.add_format(
            {
                "text_wrap": True,
                "valign": "top",
                "align": "left",
                "border": 1,
            }
        )
        # Columns
        worksheet.set_column("A:A", 40)  # Product
        worksheet.set_column("B:B", 25)  # Lot
        worksheet.set_column("C:C", 15)  # Quantity done
        # Headers
        worksheet.merge_range("A1:C1", f"Picking: {picking.name}", title_format)
        worksheet.write("A3", "Product", header_format)
        worksheet.write("B3", "Lot/Serial Number", header_format)
        worksheet.write("C3", "Quantity", header_format)
        # Data
        row = 3
        for ml in picking.move_line_ids_without_package.filtered(
            lambda ml: ml.lot_id or ml.lot_name
        ):
            worksheet.write(row, 0, ml.product_id.display_name, cell_format)
            worksheet.write(row, 1, ml.lot_id.name or "", cell_format)
            worksheet.write(row, 2, ml.quantity or 0.0, cell_format)
            row += 1
        workbook.close()
        output.seek(0)
        return output.read()
