# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

try:
    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    class ReportXlsx(object):
        def __init__(self, *args, **kwargs):
            pass


class StockPickingXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, pickings):
        # add the worksheet
        worksheet = workbook.add_worksheet('stock picking')

        # set the column size
        worksheet.set_column(0, 0, 12)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 2, 20)
        worksheet.set_column(3, 3, 12)
        worksheet.set_column(4, 4, 9)

        # set the workbook format
        bold = workbook.add_format({'bold': True,
                                    'font_name': 'Arial',
                                    'font_size': '10'})
        right_alignment = workbook.add_format({'bold': True, 'align': 'right',
                                               'font_name': 'Arial',
                                               'font_size': '10'})
        datetime_format = workbook.add_format({'num_format':
                                               'mm/dd/yyyy hh:mm AM/PM',
                                               'align': 'right',
                                               'font_name': 'Arial',
                                               'font_size': '10'})
        fontsize_format = workbook.add_format({'font_name': 'Arial',
                                               'font_size': '10'})

        row = 1
        for pick in pickings:

            worksheet.write_string(row, 0, 'Origin', bold)
            worksheet.write_string(row, 1, 'Creation Date', right_alignment)
            worksheet.write_string(row, 2, 'Name', bold)
            worksheet.write_string(row, 3, 'Backorder of', bold)
            row += 1

            # set the Datetime Format
            date_time = datetime.strptime(pick.date, '%Y-%m-%d %H:%M:%S')

            worksheet.write_string(row, 0, pick.origin or '', fontsize_format)
            worksheet.write_datetime(row, 1, date_time or '',
                                     datetime_format)
            worksheet.write_string(row, 2, pick.name or '', fontsize_format)
            worksheet.write_string(row, 3, pick.backorder_id.name or '',
                                   fontsize_format)
            row += 2

            worksheet.write_string(row, 1, 'Product Name', bold)
            worksheet.write_string(row, 2, 'Product Code', bold)
            worksheet.write_string(row, 3, 'Quantity', right_alignment)
            worksheet.write_string(row, 4, 'Uom', bold)
            row += 1

            for move in pick.move_lines:
                worksheet.write_string(row, 1, move.product_id.name or '',
                                       fontsize_format)
                worksheet.write_string(row, 2,
                                       move.product_id.default_code or '',
                                       fontsize_format)
                worksheet.write_number(row, 3, move.product_uom_qty or '',
                                       fontsize_format)
                worksheet.write_string(row, 4,
                                       move.product_id.uom_id.name or '',
                                       fontsize_format)
                row += 1
            row += 2


StockPickingXlsx('report.stock.picking.xlsx', 'stock.picking')
