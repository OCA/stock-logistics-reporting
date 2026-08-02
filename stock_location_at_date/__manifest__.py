{
    "name": "Location-Wise Inventory At Date Report",
    "version": "19.0.1.0.0",
    "category": "Inventory/Reporting",
    "summary": "Location-wise backdated stock and valuation report",
    "author": "Metamorphosis Ltd., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "maintainers": ["nsrshishir"],
    "license": "AGPL-3",
    "depends": ["stock", "stock_account", "product"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/stock_location_at_date_wizard_views.xml",
        "views/stock_location_at_date_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
