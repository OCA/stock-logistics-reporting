# Copyright 2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock Quant History",
    "summary": "Re-generate stock quants for given date",
    "version": "17.0.1.1.0",
    "license": "AGPL-3",
    "author": "Pierre Verkest <pierreverkest84@gmail.com>, Foodles, Stéphane Mangin "
    "<stephane.mangin@foodles.com>, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-reporting",
    "depends": ["stock"],
    "maintainers": [
        "petrus-v",
        "StephaneMangin",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/stock-quant-history-snapshot.xml",
        "views/stock-quant-history.xml",
        "views/res_config_settings_views.xml",
    ],
}
