# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Stock Picking Group By Partner By Carrier Sale Line Position",
    "summary": "Glue module for sale position and delivery report grouped",
    "version": "13.0.1.0.0",
    "category": "Delivery",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "depends": [
        "delivery_line_sale_line_position",
        "stock_picking_group_by_partner_by_carrier",
    ],
    "data": ["report/report_deliveryslip.xml"],
    "installable": True,
    "auto_install": True,
}
