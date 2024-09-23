# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Average Daily Sale",
    "summary": """
        Allows to gather delivered products average on daily basis""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "depends": [
        "sale",
        "stock_storage_type_putaway_abc",
        "product_abc_classification",
        "product_route_mto",
        "stock_location_zone",
    ],
    "data": [
        "security/stock_average_daily_sale_config.xml",
        "security/stock_average_daily_sale.xml",
        "views/stock_average_daily_sale_config.xml",
        "views/stock_average_daily_sale.xml",
        "views/stock_warehouse.xml",
        "data/ir_cron.xml",
    ],
    "demo": [
        "demo/stock_average_daily_sale_config.xml",
    ],
}
