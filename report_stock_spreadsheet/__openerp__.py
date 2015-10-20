# -*- coding: utf-8 -*-
# © <2015> <Miguel Chuga>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################
#
#    Copyright (C) 2015 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Report Stock',
    'version': '0.1',
    'website': 'https://mcsistemas.net',
    'category': 'Report',
    'summary': 'Generate stock to xls',
    'description': """
This module generate stock in locations to xls

""",
    'author': 'Miguel Chuga',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'stock'
    ],
    'data': [
        'report/generate_stock_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
}
