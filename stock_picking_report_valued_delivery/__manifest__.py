# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Valued Picking Report - Delivery",
    "summary": "Valued Picking Report - Compatibility fix with the Delivery module",
    "version": "16.0.1.0.0",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": ["delivery", "stock_picking_report_valued"],
    "data": ["report/stock_picking_report_valued.xml"],
    "installable": True,
    "auto_install": True,
}
