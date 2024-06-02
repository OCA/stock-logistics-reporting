# Copyright 2020 Sergio Teruel - Tecnativa <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock picking report undelivered products",
    "summary": "Display on picking report delivery slip undelivered products",
    "version": "15.0.1.0.0",
    "author": "Tecnativa,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse",
    "license": "AGPL-3",
    "depends": ["stock"],
    "data": [
        "views/product_views.xml",
        "views/report_deliveryslip.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_view.xml",
    ],
    "installable": True,
}
