# Copyright (C) 2025-Today:
# Dinamiche Aziendali Srl (<http://www.dinamicheaziendali.it/>)
# @author: Giuseppe Borruso <gborruso@dinamicheaziendali.it>
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

{
    "name": "Stock Negative Alert by Email",
    "version": "14.0.1.0.0",
    "summary": "Manage negative in stock via email alert",
    "author": "Giuseppe Borruso - Dinamiche Aziendali srl, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": [
        "base",
        "stock",
    ],
    "data": [
        "data/ir_cron_data.xml",
        "views/res_config_setting_view.xml",
    ],
    "installable": True,
    "images": ["static/description/icon.png"],
}
