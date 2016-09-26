# -*- coding: utf-8 -*-
# © 2016 - I.A.S. Ingenieria, Aplicaciones y Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Analysis",
    "summary": "Analysis view for stock",
    "version": "9.0.1.3",
    "category": "Inventory, Logistic, Storage",
    "website": "http://www.ias.com.co/",
    "author": "I.A.S. Ingenieria, Aplicaciones y Software",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
    ],
    "data": [
        'report/stock_analysis_view.xml',
        'security/ir.model.access.csv',
    ],
    'images': [
        'images/demo_analysis.png',
    ],
}
