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
    'name': 'Pickup date on delivery order',
    'version': '0.1',
    'author': 'Savoir-faire Linux',
    'maintainer': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    'license': 'AGPL-3',
    'category': 'Sales Management',
    'summary': 'Pickup date on delivery order',
    'description': """
Add a pickup date on the Delivery Orders
========================================

By default, there is 3 dates on the Delivery Orders :
- Creation date : when was this delivery order created;
- Scheduled time : when was this delivery order planed to be delivered; which \
date has been announced to the customer
- Date of Transfer : when was this delivery order completed

Hence, for internal purpose, we need a 4th date to plan and schedule the \
orders.

Contributors
------------
* Mathieu Benoit <mathieu.benoit@savoirfairelinux.com>
""",
    'depends': [
        'sale',
        'delivery',
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        'stock_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
