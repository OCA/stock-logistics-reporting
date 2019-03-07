# Copyright 2014 Pedro M. Baeza - Tecnativa <pedro.baeza@tecnativa.com>
# Copyright 2015 Antonio Espinosa - Tecnativa <antonio.espinosa@tecnativa.com>
# Copyright 2016 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# Copyright 2017 David Vidal - Tecnativa <david.vidal@tecnativa.com>
# Copyright 2017 Luis M. Ontalba - Tecnativa <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Valued Picking Report",
    "summary": "Adding Valued Picking on Delivery Slip report",
    "version": "11.0.1.0.0",
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    "website": "https://www.tecnativa.com",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": [
        "sale_management",
        "stock",
    ],
    "data": [
        'views/res_partner_view.xml',
        'report/stock_picking_report_valued.xml',
    ],
    "installable": True,
}
