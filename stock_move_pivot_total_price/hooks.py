import logging

from odoo import tools
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def create_column_product_total_price(cr):
    if not column_exists(cr, "stock_move", "product_total_price"):
        _logger.info("Initializing column product_total_price on table stock_move")
        tools.create_column(
            cr=cr,
            tablename="stock_move",
            columnname="product_total_price",
            columntype="float",
            comment="Total Product Price",
        )
        cr.execute(
            """
            WITH product_prices AS (
                SELECT
                    pt.id AS product_id,
                    sm.id AS stock_move_id,
                    (pt.list_price
                    + (COALESCE(SUM(pav.default_extra_price), 0)
                    + COALESCE(SUM(ptav.price_extra), 0)))
                    * SUM(sm.quantity) AS total_price
                FROM product_template pt
                INNER JOIN product_product as pp ON pp.product_tmpl_id = pt.id
                LEFT JOIN product_variant_combination pvc ON
                pt.id = pvc.product_product_id
                LEFT JOIN product_template_attribute_value ptav ON
                pvc.product_template_attribute_value_id = ptav.id
                LEFT JOIN product_attribute_value pav ON
                ptav.product_attribute_value_id = pav.id
                LEFT JOIN stock_move sm ON sm.product_id = pp.id
                GROUP BY pt.id, pt.list_price, sm.id
            )
            UPDATE stock_move sm
            SET product_total_price = pp.total_price
            FROM product_prices pp
            WHERE sm.id = pp.stock_move_id;
        """
        )


def pre_init_hook(env):
    create_column_product_total_price(env.cr)
