# Copyright 2019 C2i Change 2 improve - Eduardo Magdalena <emagdalena@c2i.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Picking Comments",
    "summary": "Comments texts templates on Picking documents",
    "version": "12.0.1.0.0",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "author": "C2i Change 2 improve,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "stock",
        "sale",
        "base_comment_template",
    ],
    "data": [
        'views/base_comment_template_view.xml',
        'views/report_picking.xml',
        'views/report_delivery_document.xml',
        "views/stock_picking_view.xml",
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
