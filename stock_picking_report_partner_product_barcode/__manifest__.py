# Copyright 2026 NICO SOLUTIIONS - ENGERINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Stock Picking Report Partner Product Barcode",
    "summary": "Display product barcodes on delivery slip "
    "reports based on partner settings",
    "version": "19.0.1.0.0",
    "development_status": "Beta",
    "category": "Inventory/Delivery",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "NICO SOLUTIONS - ENGINEERING & IT, Odoo Community Association (OCA)",
    "maintainers": ["NICO-SOLUTIONS"],
    "license": "AGPL-3",
    "depends": ["stock"],
    "data": [
        "report/report_deliveryslip.xml",
        "views/res_partner.xml",
    ],
}
