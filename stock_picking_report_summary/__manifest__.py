# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Quentin DUPONT (quentin.dupont@grap.coop)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Picking Report Summary",
    "summary": "Stock Picking Report Summary",
    "version": "16.0.1.0.0",
    "author": "Grap, " "Odoo Community Association (OCA)",
    "maintainers": ["quentinDupont", "legalsylvain"],
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": [
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "reports/report_print_picking_summary.xml",
        "reports/report_print_picking_summary_template.xml",
        "wizards/view_picking_summary_wizard.xml",
    ],
    "installable": True,
}
