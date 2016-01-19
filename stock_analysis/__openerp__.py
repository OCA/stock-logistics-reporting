# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Analysis",
    "summary": "Analysis view for stock",
    "version": "8.0.1.0.0",
    "category": "Inventory, Logistic, Storage",
    "website": "https://www.agilebg.com",
    "author": "Agile Business Group, Odoo Community Association (OCA)",
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
