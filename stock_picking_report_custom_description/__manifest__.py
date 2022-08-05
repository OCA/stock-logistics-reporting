# Copyright 2017 Tecnativa - Carlos Dauden
# Copyright 2018 Tecnativa - Vicent Cubells
# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Picking Report Custom Description",
    "summary": "Show moves description in picking reports",
    "version": "14.0.1.0.0",
    "category": "Warehouse",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "development_status": "Production/Stable",
    "maintainers": ["carlosdauden"],
    "license": "AGPL-3",
    "depends": [
        "stock",
    ],
    "data": [
        "views/report_deliveryslip.xml",
        "views/report_stockpicking_operations.xml",
        "views/stock_report.xml",
    ],
}
