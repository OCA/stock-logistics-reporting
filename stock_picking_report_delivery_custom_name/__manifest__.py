# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Hidden product names in pickings",
    "summary": "Allows to hide the product display name in favor of the picking description",
    "version": "16.0.1.0.1",
    "development_status": "Alpha",
    "category": "Inventory/Delivery",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["chienandalu"],
    "license": "LGPL-3",
    "depends": [
        "stock",
    ],
    "data": [
        "views/report_deliveryslip.xml",
    ],
}
