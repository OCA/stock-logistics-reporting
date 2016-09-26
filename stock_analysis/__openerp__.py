# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group - I.A.S. Ingenieria, Aplicaciones y Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Analysis",
    "summary": "Analysis view for stock",
    "version": "1.1",
    "category": "Inventory, Logistic, Storage",
    "website": "https://www.agilebg.com - http://www.ias.com.co/",
    "author": "Agile Business Group, Odoo Community Association (OCA), \
                I.A.S. Ingenieria, Aplicaciones y Software",
    "license": "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': True,
    "depends": [
        "base", "stock",
    ],
    "data": [
        'views/stock_analysis_view.xml',
        'security/ir.model.access.csv',
    ],
    'images': [
        'images/demo_analysis.png',
    ],
}
