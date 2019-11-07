# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models

_logger = logging.getLogger(__name__)


class ReportStockCardReportXlsx(models.TransientModel):
    _name = 'report.stock_card_report.report_stock_card_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        self._define_formats(workbook)
        products = objects.results.mapped('product_id')
        for product in products:
            for ws_params in self._get_ws_params(workbook, data, product):
                ws_name = ws_params.get('ws_name')
                ws_name = self._check_ws_name(ws_name)
                ws = workbook.add_worksheet(ws_name)
                generate_ws_method = getattr(
                    self, ws_params['generate_ws_method'])
                generate_ws_method(
                    workbook, ws, ws_params, data, objects, product)

    def _get_ws_params(self, wb, data, product):

        stock_card_template = {
            '1_date': {
                'header': {
                    'value': 'Date',
                },
                'data': {
                    'value': self._render('date'),
                    'type': 'datetime',
                    'format': self.format_tcell_date_left,
                },
                'width': 25,
            },
            '2_reference': {
                'header': {
                    'value': 'Reference',
                },
                'data': {
                    'value': self._render('reference'),
                },
                'width': 25,
            },
            '3_input': {
                'header': {
                    'value': 'Input',
                },
                'data': {
                    'value': self._render('input'),
                    'format': self.format_tcell_amount_right,
                },
                'width': 20,
            },
            '4_output': {
                'header': {
                    'value': 'Output',
                },
                'data': {
                    'value': self._render('output'),
                    'format': self.format_tcell_amount_right,
                },
                'width': 20,
            },
            '5_balance': {
                'header': {
                    'value': 'Balance',
                },
                'data': {
                    'value': self._render('balance'),
                    'format': self.format_tcell_amount_right,
                },
                'width': 20,
            },
        }

        ws_params = {
            'ws_name': product.name,
            'generate_ws_method': '_stock_card_report',
            'title': 'Stock Card Report - '+product.name,
            'wanted_list': [k for k in sorted(stock_card_template.keys())],
            'col_specs': stock_card_template,
        }
        return [ws_params]

    def _stock_card_report(self, wb, ws, ws_params, data, objects, product):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params, True)

        for o in objects:
            ws.write_row(
                row_pos, 0, ['Date from', 'Date to', 'Location'],
                self.format_theader_blue_center)
            ws.write_row(row_pos+1, 0, [o.date_from or '', o.date_to or ''],
                         self.format_tcell_date_center)
            ws.write_row(row_pos+1, 2, [o.location_id.name or ''],
                         self.format_tcell_center)

            row_pos += 3
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='header',
                default_format=self.format_theader_blue_center)
            ws.freeze_panes(row_pos, 0)

            balance = o._get_initial(o.results.filtered(
                lambda l: l.product_id == product and l.is_initial))
            ws.write_row(row_pos, 0, ['', 'Initial', '', ''],
                         self.format_tcell_center,)
            ws.write(row_pos, 4, balance, self.format_tcell_amount_right,)
            row_pos += 1
            product_lines = o.results.filtered(
                lambda l: l.product_id == product and not l.is_initial)
            for line in product_lines:
                balance += line.product_in - line.product_out
                row_pos = self._write_line(
                    ws, row_pos, ws_params, col_specs_section='data',
                    render_space={
                        'date': line.date or '',
                        'reference': line.reference or '',
                        'input': line.product_in or 0.000,
                        'output': line.product_out or 0.000,
                        'balance': balance,
                    },
                    default_format=self.format_tcell_left)
