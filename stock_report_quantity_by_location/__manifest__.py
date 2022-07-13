# Copyright 2019-21 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Report Quantity By Location",
    "summary": "Stock Report Quantity By Location",
    "version": "15.0.1.0.0",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": ["product", "stock"],
    "data": [
        "wizards/stock_report_quantity_by_location_views.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
