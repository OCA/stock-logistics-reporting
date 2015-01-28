# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2015 Antiun Ingenieria (http://www.antiun.com)
#                       Antonio Espinosa <antonioea@antiun.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Valued picking list",
    "version": "1.0",
    "author": "Serv. Tecnol. Avanzados - Pedro M. Baeza",
    "website": "www.serviciosbaeza.com",
    "category": "Warehouse Management",
    "description": """
Valued pickings
===============

Add amount information to picking list report and delivery order view.

You can select at partner level if picking list report must be valued or not.
""",
    "license": "GPL-3",
    "depends": [
        "base",
        "account",
        "stock",
        "sale",
        "delivery",
    ],
    "data": [
        'views/res_partner_view.xml',
        'views/stock_picking_view.xml',
        'report/stock_valued_report.xml',
    ],
    "installable": True
}
