# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.tools.sql import column_exists, create_column

_logger = logging.getLogger(__name__)


def _fill_value_signed(cr):
    cr.execute(
        """
        UPDATE stock_move
        SET value_signed = CASE
            WHEN is_in THEN COALESCE(value, 0)
            WHEN is_out THEN -COALESCE(value, 0)
            ELSE 0
        END
        """
    )


def pre_init_hook(env):
    # Create and fill the column with SQL, so that the ORM does not recompute
    # the field for every existing stock move.
    if column_exists(env.cr, "stock_move", "value_signed"):
        return
    _logger.info("Initializing column value_signed on table stock_move")
    create_column(env.cr, "stock_move", "value_signed", "numeric")
    _fill_value_signed(env.cr)
