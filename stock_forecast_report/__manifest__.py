# Copyright 2021 Odoo S.A.
# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Stock Forecast Report",
    "summary": "Backport of core 14.0 Forecast Report",
    "version": "12.0.1.0.0",
    "category": "Inventory",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["stock"],
    "data": [
        "reports/report_stock_quantity.xml",
        "security/ir.model.access.csv",
    ],
}
