# Copyright 2019 ForgeFlow S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Quantity History Location",
    "summary": "Provides stock quantity by location on past date",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "depends": ["stock"],
    "data": ["wizards/stock_quantity_history.xml"],
    "assets": {
        "web.assets_backend": [
            "stock_quantity_history_location/static/src/js/inventory_report.js",
        ],
        "web.assets_qweb": [
            "stock_quantity_history_location/static/src/xml/inventory_report.xml",
        ],
    },
}
