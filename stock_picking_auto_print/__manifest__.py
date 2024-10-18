# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Picking Auto Print",
    "summary": "Print picking delivery slip automatically after validation",
    "version": "15.0.1.0.0",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": ["stock", "web_ir_actions_act_multi"],
    "data": [
        "views/stock_picking_type_views.xml",
    ],
    "installable": True,
}
