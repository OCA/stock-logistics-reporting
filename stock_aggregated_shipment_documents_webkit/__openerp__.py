# -*- encoding: utf-8 -*-
# ##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


{
    'name': 'Aggregated Bill oif Lading & Commercial Invoice',
    'version': '1.0',
    'category': 'Reports/Webkit',
    'description': """
Aggregated Bill of Lading & Commercial Invoice - webkit report
==============================================================

For international shipments, carriers have to present a Bill of Lading and a
Commercial Invoice to the customs.  When shipping multiple orders to the
same customer or to an intermediary Warehouse, you need to produce a unique
Bill of Ladding which aggregate all the selected Delivery Orders and a
unique commercial Invoice.

How to use this module
----------------------
In Warehouse\Delivery Orders, select all the DO you want to print; in the Print
button, select the report 'Aggregated shipment documents'.

Constraints
-----------
- this report will be printed only if all the selected Delivery Orders are
  assigned to the same partner.
- as the real invoice is not yet created, the prices displayed on the
  Commercial Invoice are the one from the partner's pricelist

Contributors
------------
* Vincent Vinet <vincent.vinet@savoirfairelinux.com>
* Mathieu Benoit <mathieu.benoit@savoirfairelinux.com>
* Based on bill_of_lading_webkit
    """,
    'author': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    'depends': [
        'base',
        'report_webkit',
        'base_headers_webkit',
        'stock',
        'delivery',
        'stock_bill_of_lading_webkit',
    ],
    'data': [
        'report.xml'
    ],
    'installable': True,
    'auto_install': False,
}
