# -*- coding: utf-8 -*-
# Copyright 2017 Luis M. Ontalba - Tecnativa <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Valued Picking Report Triple Discount",
    "summary": "Adding Triple Discount on Valued Picking Report",
    "version": "10.0.1.0.0",
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": [
        "sale_triple_discount",
        "stock_valued_picking_report",
    ],
    "data": [
        'report/stock_valued_picking_report_triple_discount.xml',
    ],
    "installable": True,
}
