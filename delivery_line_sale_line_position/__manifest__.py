# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Delivery Line Sale Line Position",
    "summary": "Adds the sale line position to the delivery report lines",
    "version": "16.0.1.0.0",
    "category": "Delivery",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "depends": ["stock", "sale_order_line_position"],
    "data": [
        "report/report_deliveryslip.xml",
        "views/stock_move.xml",
        "views/stock_picking.xml",
    ],
    "installable": True,
}
