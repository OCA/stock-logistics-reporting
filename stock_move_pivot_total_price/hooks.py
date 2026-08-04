import logging

from odoo.tools import sql
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def _backfill_product_total_price(cr):
    cr.execute(
        """
        WITH product_prices AS (
            SELECT
                pp.id AS product_product_id,
                COALESCE(pt.list_price, 0)
                    + COALESCE(SUM(ptav.price_extra), 0) AS unit_price
            FROM product_product pp
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN product_variant_combination pvc
                ON pvc.product_product_id = pp.id
            LEFT JOIN product_template_attribute_value ptav
                ON ptav.id = pvc.product_template_attribute_value_id
            GROUP BY pp.id, pt.list_price
        )
        UPDATE stock_move sm
        SET product_total_price =
            prices.unit_price * COALESCE(sm.quantity, 0)
        FROM product_prices prices
        WHERE prices.product_product_id = sm.product_id;
        """
    )


def create_column_product_total_price(cr):
    if not column_exists(cr, "stock_move", "product_total_price"):
        _logger.info("Initializing column product_total_price on table stock_move")
        sql.create_column(
            cr=cr,
            tablename="stock_move",
            columnname="product_total_price",
            columntype="float",
            comment="Total Product Price",
        )
        _backfill_product_total_price(cr)


def pre_init_hook(env):
    create_column_product_total_price(env.cr)
