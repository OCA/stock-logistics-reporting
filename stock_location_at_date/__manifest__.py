# -*- coding: utf-8 -*-
{
    'name': 'Location-Wise Inventory At Date Report',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Reporting',
    'summary': 'Location-wise backdated stock and valuation report',
    'description': """
        Location-Wise Inventory At Date Report
        =======================================
        - Read-only reporting model with table creation disabled (_auto = False).
        - Dynamic calculation of historical stock levels per internal/transit location.
        - Pre-aggregated by Location x Product x Lot x Package as of selected date.
        - Supports filtering by date, company, locations, product categories, and products.
        - High-performance UNLOGGED session table backing for Pivot, List, and Graph views.
        - Zero persistent database table storage overhead.
    """,
    'author': 'Metamorphosis Ltd., Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/stock-logistics-reporting',
    'maintainers': ['nsrshishir'],
    'license': 'AGPL-3',
    'depends': ['stock', 'stock_account', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/stock_location_at_date_wizard_views.xml',
        'views/stock_location_at_date_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
