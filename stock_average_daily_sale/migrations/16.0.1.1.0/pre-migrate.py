# Copyright 2024 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.tools.sql import column_exists, create_column

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    if not column_exists(cr, "stock_average_daily_sale_config", "exclude_weekends"):
        _logger.info("Create stock_average_daily_sale_config column exclude_weekends")
        create_column(
            cr, "stock_average_daily_sale_config", "exclude_weekends", "boolean"
        )
        cr.execute("UPDATE stock_average_daily_sale_config SET exclude_weekends = True")
