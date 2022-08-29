# © 2022 Roberto Lizana (Trey)
# License: LGPL-3 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "Print Formats Picking CMR",
    "summary": "CMR Report from Picking",
    "version": "14.0.1.0.0",
    "category": "Warehouse Management",
    "author": "Trey, " "Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "contributors": ["AshishHirapara"],
    "depends": [
        "stock",
        "web",
    ],
    "data": [
        "data/report_paperformat.xml",
        "views/report_cmr.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
    "application": True,
}
