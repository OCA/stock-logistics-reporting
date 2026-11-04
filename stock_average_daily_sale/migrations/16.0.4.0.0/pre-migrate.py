# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

RENAMED_COLUMNS = {
    "stock_average_daily_sale_config": [
        ("number_sales_qty_in_stock", "average_consumption_factor"),
    ],
}


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    openupgrade.rename_columns(env.cr, RENAMED_COLUMNS)
