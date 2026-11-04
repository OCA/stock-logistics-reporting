# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

RENAMED_COLUMNS = {
    "stock_average_daily_sale_config": [
        ("number_sales_qty_in_stock", "average_consumption_factor"),
    ],
}

RENAMED_MODELS = [
    ("stock.average.daily.sale", "stock.average.daily.usage"),
    ("stock.average.daily.sale.config", "stock.average.daily.usage.config"),
    ("stock.average.daily.sale.demo", "stock.average.daily.usage.demo"),
]

RENAMED_TABLES = [
    ("stock_average_daily_sale_config", "stock_average_daily_usage_config"),
]

RENAMED_XMLIDS = [
    (
        "stock_average_daily_sale.model_stock_average_daily_sale",
        "stock_average_daily_sale.model_stock_average_daily_usage",
    ),
    (
        "stock_average_daily_sale.model_stock_average_daily_sale_config",
        "stock_average_daily_sale.model_stock_average_daily_usage_config",
    ),
    (
        "stock_average_daily_sale.model_stock_average_daily_sale_demo",
        "stock_average_daily_sale.model_stock_average_daily_usage_demo",
    ),
    (
        "stock_average_daily_sale.stock_average_daily_sale_config_level_a",
        "stock_average_daily_sale.stock_average_daily_usage_config_level_a",
    ),
    (
        "stock_average_daily_sale.stock_average_daily_sale_config_level_b",
        "stock_average_daily_sale.stock_average_daily_usage_config_level_b",
    ),
    (
        "stock_average_daily_sale.stock_average_daily_sale_config_level_c",
        "stock_average_daily_sale.stock_average_daily_usage_config_level_c",
    ),
    (
        "stock_average_daily_sale.stock_average_daily_sale_access_user",
        "stock_average_daily_sale.stock_average_daily_usage_access_user",
    ),
    (
        "stock_average_daily_sale.stock_average_daily_sale_config_access_user",
        "stock_average_daily_sale.stock_average_daily_usage_config_access_user",
    ),
    (
        "stock_average_daily_sale.stock_average_daily_sale_config_access_manager",
        "stock_average_daily_sale.stock_average_daily_usage_config_access_manager",
    ),
    (
        "stock_average_daily_sale.stock_average_daily_sale_company_rule",
        "stock_average_daily_sale.stock_average_daily_usage_company_rule",
    ),
    (
        "stock_average_daily_sale.stock_average_daily_sale_config_company_rule",
        "stock_average_daily_sale.stock_average_daily_usage_config_company_rule",
    ),
    (
        "stock_average_daily_sale.stock_average_daily_sale_demo_access_user",
        "stock_average_daily_sale.stock_average_daily_usage_demo_access_user",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    _logger.info("Dropping legacy materialized view stock_average_daily_sale...")
    env.cr.execute("DROP MATERIALIZED VIEW IF EXISTS stock_average_daily_sale CASCADE;")

    openupgrade.rename_columns(env.cr, RENAMED_COLUMNS)
    openupgrade.rename_tables(env.cr, RENAMED_TABLES)
    openupgrade.rename_models(env.cr, RENAMED_MODELS)
    openupgrade.rename_xmlids(env.cr, RENAMED_XMLIDS)

    env.cr.execute(
        """
        UPDATE ir_config_parameter
        SET key = 'stock_average_daily_usage_refresh_date'
        WHERE key = 'stock_average_daily_sale_refresh_date';
        """
    )
