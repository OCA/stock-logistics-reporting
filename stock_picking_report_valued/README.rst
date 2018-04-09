.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===========================
Stock Picking Report Valued
===========================

Add amount information to Delivery Slip report.
You can select at partner level if picking list report must be valued or not.
If the picking is done it's valued with quantity done, otherwise the picking
is valued with reserved quantity.

Configuration
=============

#. Go to *Customers > (select one of your choice) > Sales & Purchases*.
#. Set *Valued picking* field on.

Usage
=====

To get the stock picking valued report:

#. Create a Sale Order with stockable products a *Valued picking* able
   customer.
#. Confirm the Sale Order.
#. Click on *Deliveries* stat button.
#. Go to *Print > Delivery Slip*.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/151/11.0

Known issues / Roadmap
======================

* If the picking is not reserved, values aren't computed.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/stock-logistics-reporting/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Antonio Espinosa <antonio.espinosa@tecnativa.com>
* Oihane Crucelaegui <oihane.crucelaegi@avanzosc.es>
* Carlos Dauden <carlos.dauden@tecnativa.com>
* David Vidal <david.vidal@tecnativa.com>
* Luis M. Ontalba <luis.martinez@tecnativa.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
