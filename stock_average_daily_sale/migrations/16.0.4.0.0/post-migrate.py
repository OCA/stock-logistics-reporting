# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    # In previous versions, both average daily and average sale were active
    # by default. Enable both strategies on existing configs to preserve behavior.
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE stock_average_daily_sale_config
        SET use_average_daily_strategy = TRUE,
            use_average_consumption_strategy = TRUE
        """,
    )
