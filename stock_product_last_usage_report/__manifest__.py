# Copyright 2018 Odoo, S.A.
# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Stock Product Last Usage Report",
    "version": "11.0.1.0.0",
    "author": "Odoo S.A., "
              "Eficent, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "license": "LGPL-3",
    "depends": [
        "stock",
    ],
    "data": [
        'report/report_stock_lines_date_views.xml',
    ],
    "installable": True,
}
