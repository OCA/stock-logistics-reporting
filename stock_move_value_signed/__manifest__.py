# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Move Value Signed",
    "summary": "Signed value of stock moves in the Moves Analysis report",
    "version": "19.0.1.0.0",
    "category": "Warehouse",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["ivantodorovich"],
    "license": "AGPL-3",
    "installable": True,
    "depends": ["stock_account"],
    "data": ["views/stock_move_views.xml"],
    "pre_init_hook": "pre_init_hook",
}
