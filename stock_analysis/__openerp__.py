# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group - I.A.S. Colombia.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Analysis",
    "summary": "Analysis view for stock",
    "version": "9.0.1.0.0",
    "category": "Warehouse Management",
    "website": "https://www.agilebg.com",
    "author": "Agile Business Group,"
              "Odoo Community Association (OCA),"
              "I.A.S. Colombia",
    "license": "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': True,
    "depends": [
        "stock",
    ],
    "data": [
        'views/stock_analysis_view.xml',
        'security/ir.model.access.csv',
    ],
    'images': [
        'images/demo_analysis.png',
    ],
}
