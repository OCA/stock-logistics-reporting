{
    "name": "Stock Picking Report Printed Flag",
    "summary": "Adds printed flag support to stock picking",
    "version": "17.0.1.0.0",
    "category": "Stock",
    "license": "AGPL-3",
    "author": "Binhex Systems Solutions S.L, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "depends": [
        "stock",
        "report_printed_flag",
    ],
    "data": [
        "views/stock_picking_views.xml",
    ],
    "installable": True,
    "application": False,
    "development_status": "Alpha",
    "images": ["static/description/icon.png"],
}
