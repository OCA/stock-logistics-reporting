# -*- coding: utf-8 -*-
import werkzeug
from werkzeug.exceptions import InternalServerError
from io import BytesIO
from odoo import http
from odoo.http import request
from odoo.tools.misc import html_escape

import json


class StockCardReportController(http.Controller):

  @http.route('/stock/stock_card_report/<string:output_format>', type='http', auth='user')
  def report(self, output_format, report_name=False, **kw):
    if output_format == 'pdf':
      report_ref = request.env.ref('stock_card_report.action_stock_card_report_pdf')
      method_name = '_render_qweb_pdf'
      report = getattr(report_ref, method_name)(
          report_ref,
          res_ids=[int(kw['active_id'])],
          data={
              'report_type': 'pdf'
          },
      )[0]
      return request.make_response(
          report,
          headers=[
              ('Content-Type', 'application/pdf'),
              ('Content-Disposition', f'attachment; filename= Stock_Card_Report.pdf'),
          ],
      )
    else:
      report_ref = request.env.ref('stock_card_report.action_stock_card_report_xlsx')
      method_name = '_render_xlsx'
      report = getattr(report_ref, method_name)(
          report_ref,
          docids=[int(kw['active_id'])],
          data={
              'report_type': 'xlsx'
          },
      )[0]
      return request.make_response(
          report,
          headers=[
              ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
              ('Content-Disposition', 'attachment; filename= Stock_Card_Report.xlsx'),
          ],
      )
