# Copyright 2018-2021 ForgeFlow S.L.
# Copyright 2018 Aleph Objects, Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Account Valuation Report",
    "version": "12.0.1.0.0",
    "summary": "Improves logic of the Inventory Valuation Report",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "depends": ["stock_account"],
    "license": "AGPL-3",
    "data": [
        "views/product_product_views.xml",
        "wizards/stock_quantity_history_view.xml",
    ],
    'installable': True,
}
