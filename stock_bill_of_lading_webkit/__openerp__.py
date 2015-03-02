# -*- encoding: utf-8 -*-
###############################################################################
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
    'name': 'Bill of Lading using Webkit Library',
    'version': '1.0',
    'category': 'Reports/Webkit',
    'description': """

A Bill of Lading is a document issued by a carrier to a shipper of goods.
It is a negotiable instrument, and it serves three purposes:
 - it is a receipt for the goods shipped;
 - it evidences the contract of carriage;
 - it serves as a document of title (i.e. ownership).

This document could be different from a Delivery Order as it has some legal
issues.

Two reports are provided in this module
 - Bill of Lading for Delivey Orders;
 - Bill of Lading for Incoming Shipment (the use-case is shipment from an
 international Warehouse
to the local Warehouse).

This module also add a new field for a warehouse to pick form or deliver to;
this field will be used if the default warehouse_id is not set
(normally from a PO).

Contributors
------------
* Marc Cassuto (marc.cassuto@savoirfairelinux.com)
* Mathieu Benoit (mathieu.benoit@savoirfairelinux.com)
* Camptocamp with its original module stock_picking_webkit
    """,
    'author': "Savoir-faire Linux,Odoo Community Association (OCA)",
    'website': 'http://www.savoirfairelinux.com',
    'depends': [
        'base',
        'report_webkit',
        'base_headers_webkit',
        'stock',
        'delivery'
    ],
    'data': ['report.xml', 'stock_view.xml'],
    'installable': True,
    'auto_install': False,
}
