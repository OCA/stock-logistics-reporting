# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Report Quantity By Location",
    "summary": "Stock Report Quantity By Location",
    "version": "12.0.1.0.0",
    "author": "Eficent, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": [
        "product",
        "stock",
    ],
    "data": [
        'wizards/stock_report_quantity_by_location_views.xml',
    ],
    "installable": True,
}
