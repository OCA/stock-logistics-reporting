# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Stock Inventory Valuation Report',
    'summary': 'Add report button on Inventory Valuation.',
    'version': '12.0.1.1.1',
    'category': 'Warehouse',
    'website': 'https://github.com/OCA/stock-logistics-reporting',
    'author': 'Ecosoft,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'depends': [
        'stock_account',
        'report_xlsx_helper',
    ],
    'data': [
        'data/paper_format.xml',
        'data/report_data.xml',
        'reports/stock_inventory_valuation_report.xml',
        'wizard/stock_quantity_history_view.xml',
    ],
    'installable': True,
}
