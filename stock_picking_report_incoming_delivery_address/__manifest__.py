# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Stock Picking Report Incoming Delivery Address",
    "summary": "Allow show delivery address in report when picking type is incoming",
    "version": "16.0.1.0.1",
    "development_status": "Alpha",
    "category": "Uncategorized",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["EmilioPascual", "rafaelbn"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
    ],
    "data": [
        "views/stock_picking_type.xml",
        "views/report_deliveryslip.xml",
        "views/report_stockpicking_operations.xml",
    ],
}
