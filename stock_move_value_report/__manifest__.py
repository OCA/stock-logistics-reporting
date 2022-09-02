# Copyright 2019 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Move Cost Value Report",
    "version": "15.0.1.0.0",
    "category": "Warehouse",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["stock_account"],
    "data": [
        "report/stock_value_report.xml",
        "report/stock_move_line_value_report.xml",
        "report/stock_move_value_report.xml",
        "report/stock_picking_value_report.xml",
        "report/stock_scrap_value_report.xml",
        "report/stock_inventory_value_report.xml",
    ],
}
