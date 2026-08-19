# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Stock Quantity",
    "version": "19.0.1.0.0",
    "summary": "Track the stock quantity behind valuation journal items",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "depends": ["stock_account"],
    "license": "AGPL-3",
    "data": [
        "views/account_move_line_views.xml",
    ],
    "installable": True,
}
