# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Product Demand Info",
    "summary": "Past demand by configurable periods on product and orderpoint",
    "version": "19.0.1.1.0",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "maintainers": ["ivantodorovich"],
    "license": "AGPL-3",
    "category": "Inventory",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/product_demand_period_data.xml",
        "views/product_demand_period_views.xml",
        "views/product_template_views.xml",
        "views/stock_warehouse_orderpoint_views.xml",
        "views/res_config_settings.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "stock_product_demand_info/static/src/**/*.js",
            "stock_product_demand_info/static/src/**/*.xml",
        ],
    },
}
