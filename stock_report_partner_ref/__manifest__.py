{
    "name": "Stock Report Partner Ref",
    "summary": "Adds customer reference to stock picking reports",
    "version": "17.0.1.0.0",
    "category": "Stock",
    "license": "AGPL-3",
    "author": "Binhex Systems Solutions S.L, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "depends": [
        "stock",
        "sale_stock",
    ],
    "data": [
        "views/partner_ref.xml",
        "views/report_delivery.xml",
        "views/report_picking.xml",
    ],
    "installable": True,
    "application": False,
    "maintainers": ["Binhex Systems Solutions S.L"],
    "development_status": "Alpha",
}
