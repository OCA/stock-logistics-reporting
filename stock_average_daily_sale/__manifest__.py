# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Average Daily Sale",
    "summary": """
        Allows to gather delivered products average on daily basis""",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,BCIM,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "depends": [
        "sale",
        "stock_storage_type_putaway_abc",
        "product_route_mto",
    ],
    "data": [
        "security/stock_average_daily_sale_config.xml",
        "security/stock_average_daily_sale.xml",
        "security/stock_average_daily_sale_demo.xml",
        "views/stock_average_daily_sale_config.xml",
        "views/stock_average_daily_sale.xml",
        "views/stock_warehouse.xml",
        "data/ir_cron.xml",
    ],
    "external_dependencies": {"python": ["freezegun"]},
    "demo": [
        "demo/stock_average_daily_sale_config.xml",
        "demo/stock_move.xml",
    ],
}
