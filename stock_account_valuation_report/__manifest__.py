# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
#   (<https://www.eficent.com>)
# Copyright 2018 Aleph Objects, Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Account Valuation Report",
    "version": "13.0.1.0.0",
    "summary": "Improves logic of the Inventory Valuation Report",
    "author": "Eficent, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "depends": ["stock_account"],
    "license": "AGPL-3",
    "data": [
        "views/stock_valuation_layer_views.xml",
        "views/account_move_line_view.xml",
    ],
    "installable": True,
}
