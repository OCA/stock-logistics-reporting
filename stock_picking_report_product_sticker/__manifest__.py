# Copyright 2023 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Stock Picking Report - Product Sticker",
    "version": "15.0.1.0.2",
    "author": "Moduon, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Stock",
    "depends": [
        "product_sticker",
        "stock",
    ],
    "data": [
        "views/stock_picking_type_views.xml",
        "views/stock_picking_views.xml",
        "report/report_deliveryslip.xml",
        "data/menus.xml",
    ],
    "maintainers": ["Shide"],
    "installable": True,
}
