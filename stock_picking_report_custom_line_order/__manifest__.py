# Copyright 2025 Foodles (https://www.foodles.co/).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Picking Report Custom Line Order",
    "summary": """
    Changes the way moves and move lines are fetched for the report picking so that
    other modules could customize the order of the lines in the report.
    """,
    "category": "Warehouse",
    "version": "14.0.0.0.1",
    "author": "Foodles, Odoo Community Association (OCA)",
    "maintainers": ["alexandregaldeano"],
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "license": "AGPL-3",
    "depends": [
        # Odoo
        "stock",
    ],
    "data": [
        # Reports
        "views/report_stockpicking_operations.xml",
    ],
    "application": False,
}
