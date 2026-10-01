# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info(
        "Copy 'number_days_qty_in_stock' into 'number_sales_qty_in_stock' "
        "(stock_average_daily_sale_config)..."
    )
    cr.execute(
        """
        UPDATE stock_average_daily_sale_config
        SET number_sales_qty_in_stock = number_days_qty_in_stock
        """
    )
