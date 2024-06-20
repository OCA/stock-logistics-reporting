# Copyright 2024 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Picking Operations Multilang",
    "version": "16.0.1.0.0",
    "category": "Reporting",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Quartile, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["stock"],
    "data": [
        "views/stock_warehouse_views.xml",
        "reports/picking_operations_report.xml",
        "reports/report_picking_with_language.xml",
    ],
    "uninstall_hook": "uninstall_hook",
    "installable": True,
}
