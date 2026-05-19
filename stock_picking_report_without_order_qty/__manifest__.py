# © 2023 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    "name": "Stock Picking Report Without Order Quantity",
    "summary": """
        Hide delivery slip note report quantity field
    """,
    "author": "Solvos, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "version": "18.0.1.0.0",
    "category": "Stock",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "depends": [
        "stock",
    ],
    "data": [
        "report/report_deliveryslip.xml",
    ],
    "installable": True,
}
