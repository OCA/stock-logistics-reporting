# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Stock Kardex',
    'summary': 'View and create reports',
    'category': 'Stock',
    'description': """
Stock Reports
==================
    """,
    'depends': [
        'stock'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_kardex_data.xml',
        'views/report_stock.xml',
        'views/search_template_view.xml',
        'views/res_config_settings_view.xml',
    ],
    'qweb': [
        'static/src/xml/stock_kardex_template.xml',
    ],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
