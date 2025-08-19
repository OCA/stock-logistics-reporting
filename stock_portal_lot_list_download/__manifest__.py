# Copyright 2025 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Portal Lot List Donwload",
    "summary": "Allows portal users to download lot list of delivery pickings in Excel "
    "format.",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "depends": ["sale_stock"],
    "data": [
        "views/sale_stock_portal_template.xml",
    ],
    "installable": True,
}
