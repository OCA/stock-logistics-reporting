# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    # In previous versions, both average daily and average sale were active
    # by default. Enable both strategies on existing configs to preserve behavior.
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE stock_average_daily_usage_config
            SET use_average_daily_strategy = TRUE,
                use_average_consumption_strategy = TRUE
            """,
    )
