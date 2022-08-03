# Copyright 2020 ForgeFlow S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Account Valuation Report",
    "version": "15.0.1.0.1",
    "summary": "Improves logic of the Inventory Valuation Report",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "depends": ["stock_account"],
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/product_product_views.xml",
        "wizards/stock_valuation_history.xml",
    ],
    "installable": True,
}
