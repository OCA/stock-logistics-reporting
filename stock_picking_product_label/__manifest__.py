# Copyright 2019 Eficent <patrickraymondwilson@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Print Labels in Picking',
    'summary': "Print Product Labels in a Stock Picking",
    'author': "Eficent, Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/stock-logistics-reporting",
    'category': 'Customer Relationship Management',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'stock'
        ],
    'data': [
        'reports/report_print_labels.xml',
        'reports/report_print_labels_template.xml'

    ],
    'development_status': 'Beta',
}
