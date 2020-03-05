# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models

_logger = logging.getLogger(__name__)


class ReportStockInventoryValuationReportXlsx(models.TransientModel):
    _name = 'report.s_i_v_r.report_stock_inventory_valuation_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def _get_ws_params(self, wb, data, objects):

        stock_inventory_valuation_template = {
            '1_number': {
                'header': {
                    'value': '#',
                },
                'data': {
                    'value': self._render('n'),
                },
                'width': 12,
            },
            '2_reference': {
                'header': {
                    'value': 'Reference',
                },
                'data': {
                    'value': self._render('reference'),
                },
                'width': 15,
            },
            '3_name': {
                'header': {
                    'value': 'Name',
                },
                'data': {
                    'value': self._render('name'),
                },
                'width': 36,
            },
            '4_barcode': {
                'header': {
                    'value': 'Barcode',
                },
                'data': {
                    'value': self._render('barcode'),
                },
                'width': 15,
            },
            '5_qty_at_date': {
                'header': {
                    'value': 'Quantity',
                },
                'data': {
                    'value': self._render('qty_at_date'),
                    'format': self.format_tcell_amount_conditional_right,
                },
                'width': 18,
            },
            '6_standard_price': {
                'header': {
                    'value': 'Cost',
                },
                'data': {
                    'value': self._render('standard_price'),
                    'format': self.format_tcell_amount_conditional_right,
                },
                'width': 18,
            },
            '7_stock_value': {
                'header': {
                    'value': 'Value',
                },
                'data': {
                    'value': self._render('stock_value'),
                    'format': self.format_tcell_amount_conditional_right,
                },
                'width': 18,
            },
        }

        ws_params = {
            'ws_name': 'Inventory Valuation Report',
            'generate_ws_method': '_inventory_valuation_report',
            'title': 'Inventory Valuation Report',
            'wanted_list': [k for k in sorted(
                stock_inventory_valuation_template.keys())],
            'col_specs': stock_inventory_valuation_template,
        }
        return [ws_params]

    def _inventory_valuation_report(self, wb, ws, ws_params, data, objects):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params, True)

        for o in objects:
            ws.write_row(
                row_pos, 0, ['Date', 'Partner', 'Tax ID'],
                self.format_theader_blue_center)
            ws.write_row(
                row_pos+1, 0, [o.date or ''], self.format_tcell_date_center)
            ws.write_row(
                row_pos+1, 1,
                [o.company_id.name or '', o.company_id.vat or ''],
                self.format_tcell_center)

            row_pos += 3
            row_pos = self._write_line(
                ws, row_pos, ws_params, col_specs_section='header',
                default_format=self.format_theader_blue_center)
            ws.freeze_panes(row_pos, 0)

            total = 0.00
            for line in o.results:
                row_pos = self._write_line(
                    ws, row_pos, ws_params, col_specs_section='data',
                    render_space={
                        'n': row_pos-5,
                        'name': line.name or '',
                        'reference': line.reference or '',
                        'barcode': line.barcode or '',
                        'qty_at_date': line.qty_at_date or 0.000,
                        'standard_price': line.standard_price or 0.00,
                        'stock_value': line.stock_value or 0.00,
                    },
                    default_format=self.format_tcell_left)
                total += line.stock_value

            ws.write(row_pos, 6, total, self.format_theader_blue_amount_right)
