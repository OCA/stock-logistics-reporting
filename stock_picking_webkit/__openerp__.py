# -*- coding: utf-8 -*-
##############################################################################
#
#   Copyright (c) 2011-2013 Camptocamp SA (http://www.camptocamp.com)
#   @author Nicolas Bessi
#   Copyright (c) 2013 Agile Business Group (http://www.agilebg.com)
#   @author Lorenzo Battistini
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Picking reports using Webkit Library',
    'version': '1.0.1',
    'category': 'Reports/Webkit',
    'description': """
Replaces the legacy rml picking Order report by brand new webkit reports.
Three reports are provided:
 - Aggregated pickings
 - Aggregated deliveries
 - Delivery Slip
    """,
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'website': 'http://www.openerp.com',
    'depends': ['base', 'report_webkit', 'base_headers_webkit', 'stock', 'delivery'],
    'data': ['report.xml',
             'stock_view.xml',
             ],
    'installable': False,
    'auto_install': False,
}
