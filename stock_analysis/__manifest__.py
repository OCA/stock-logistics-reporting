# © 2016 Lorenzo Battistini - Agile Business Group
# © 2020 Lorenzo Battistini - TAKOBI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Analysis",
    "summary": "Analysis view for stock",
    "version": "12.0.1.0.0",
    "development_status": "Beta",
    "category": "Warehouse",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "Agile Business Group, Odoo Community Association (OCA)",
    "maintainers": ["eLBati"],
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
