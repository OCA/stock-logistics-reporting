# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Valuation Discrepancy Adjust",
    "version": "16.0.1.0.0",
    "summary": "Implements Wizard for Adjust "
    "Discrepancies on Account Inventory Valuation",
    "category": "Warehouse Management",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "license": "AGPL-3",
    "depends": ["stock_account_valuation_report"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/wizard_stock_discrepancy_adjustment_view.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["AaronHForgeFlow"],
}
