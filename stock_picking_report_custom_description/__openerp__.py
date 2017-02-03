# -*- coding: utf-8 -*-
# Copyright 2017 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Picking Report Custom Description",
    "summary": "New report to print move description in delivery split",
    "version": "9.0.1.0.0",
    "category": "Stock",
    "website": "http://www.tecnativa.com",
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "stock",
    ],
    "data": [
        "views/report_deliveryslip.xml",
        "views/stock_report.xml",
    ],
}
