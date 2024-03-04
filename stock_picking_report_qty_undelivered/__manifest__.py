# Copyright 2024 Moduon Team S.L.
# License GPL-3.0 (https://www.gnu.org/licenses/gpl-3.0)

{
    "name": "Stock Picking Report Undelivered Quantity",
    "summary": "Print a summary of the undelivered quantity",
    "version": "16.0.1.0.1",
    "development_status": "Alpha",
    "category": "Inventory/Delivery",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["EmilioPascual"],
    "license": "GPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
    ],
    "data": [
        "views/stock_picking_type_views.xml",
        "views/report_deliveryslip.xml",
    ],
}
