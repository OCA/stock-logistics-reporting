# -*- coding: utf-8 -*-
# © <2015> <Miguel Chuga>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Report Stock Spreadsheet",
    "summary": "generates the stock of all locations",
    "version": "8.0.1.0.0",
    "category": "Report",
    "website": "https://mcsistemas.net",
    "author": "Miguel Chuga,"
              # "MC-Sistemas,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "stock",
    ],
    "data": [
        'report/generate_stock_wizard.xml',
    ],
    "demo": [
    ],
}

