# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Report Quantity By Location By Date",
    "summary": """
        This module allows to get stock reporting by location and by date.""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "depends": ["stock"],
    "data": [
        "security/security.xml",
        "wizards/stock_report_quantity_location_date.xml",
        "wizards/report_stock_quantity_location_date.xml",
    ],
    "demo": [],
}
