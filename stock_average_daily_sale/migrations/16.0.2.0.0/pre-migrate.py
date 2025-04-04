# Copyright 2024 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.tools.sql import column_exists, create_column

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    if not column_exists(cr, "stock_average_daily_sale_config", "location_id"):
        _logger.info("Create stock_average_daily_sale_config column location_id")
        create_column(cr, "stock_average_daily_sale_config", "location_id", "integer")
        cr.execute(
            """
            UPDATE stock_average_daily_sale_config
            SET location_id = (
                SELECT average_daily_sale_root_location_id
                FROM stock_warehouse
                WHERE stock_warehouse.id=stock_average_daily_sale_config.warehouse_id
            )
        """
        )
