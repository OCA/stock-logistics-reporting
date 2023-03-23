# Copyright 2023 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Stock Picking Report External Note",
    "summary": "Adds a note in Stock Picking shown on external reports like Delivery Slip",
    "version": "15.0.0.1.1",
    "development_status": "Alpha",
    "category": "Inventory/Delivery",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["Shide"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
    ],
    "data": [
        "report/report_deliveryslip.xml",
        "views/stock_picking_views.xml",
    ],
}
