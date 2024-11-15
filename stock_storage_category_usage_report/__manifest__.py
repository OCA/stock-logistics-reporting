# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Storage Category Usage Report",
    "summary": """
        This module allows to get reporting on stock storage categories
         about their locations usage""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "depends": [
        "stock",
        "stock_location_children",
        "stock_location_occupancy",
        "web_widget_progressbar_gradient",
    ],
    "data": [
        "views/stock_storage_category.xml",
    ],
}
