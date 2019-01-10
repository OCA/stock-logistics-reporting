# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Stock Quantity History Location',
    'summary': "Provides stock quantity by location on past date",
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Eficent,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/stock-logistics-reporting',
    'depends': [
        'stock',
    ],
    'data': [
        'wizards/stock_quantity_history.xml',
    ],

}
