# -*- coding: utf-8 -*-
# Copyright 2014 Pedro M. Baeza - Tecnativa <pedro.baeza@tecnativa.com>
# Copyright 2015 Antonio Espinosa - Tecnativa <antonio.espinosa@tecnativa.com>
# Copyright 2016 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# Copyright 2017 David Vidal - Tecnativa <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Valued Picking Report",
    "summary": "Adding Valued Picking on Delivery Slip report",
    "version": "10.0.1.0.1",
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    "website": "https://www.tecnativa.com",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": [
        "account",
        "stock",
        "sale",
        "delivery",
    ],
    "data": [
        'views/res_partner_view.xml',
        'report/stock_picking_valued_report.xml',
    ],
    "installable": True,
}
