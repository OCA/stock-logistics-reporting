# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Stock Picking Report Delivery Driver",
    "summary": "Delivery Driver info in Stock Picking reports",
    "version": "18.0.1.0.1",
    "development_status": "Alpha",
    "category": "Inventory/Inventory",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["Shide"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "delivery_driver",
    ],
    "data": [
        "report/report_deliveryslip.xml",
        "report/report_stockpicking_operations.xml",
    ],
}
