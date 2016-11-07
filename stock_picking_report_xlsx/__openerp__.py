# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Stock picking xlsx report',
    'version': '8.0.1.0.0',
    'summary': 'Print stock picking report in xlsx',
    'website': 'http://www.serpentcs.com',
    'author': 'Serpent Consulting Services Pvt. Ltd.,'
              'Odoo Community Association (OCA), '
              'Agile Business Group',
    'category': 'Stock',
    'license': 'AGPL-3',
    'depends': ['report_xlsx', 'stock'],
    'data': ['views/report_view.xml'],
    'installable': True,
}
