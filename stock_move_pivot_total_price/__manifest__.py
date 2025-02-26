# Copyright 2024 Bernat Obrador
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Move Pivot Total Price",
    "summary": "Adds a total price UOM to the stock move pivot view",
    "version": "17.0.1.0.0",
    "author": "Odoo Community Association (OCA), APSL-Nagarro",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Stock",
    "license": "AGPL-3",
    "depends": ["stock"],
    "maintainers": ["BernatObrador"],
    "data": [
        "views/stock_move.xml",
    ],
    "installable": True,
    "pre_init_hook": "pre_init_hook",
}
