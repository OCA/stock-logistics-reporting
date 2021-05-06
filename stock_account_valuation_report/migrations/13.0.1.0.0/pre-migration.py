# Copyright 2020 ForgeFlow <http://www.forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

from odoo.tools import sql


def fill_stock_valuation_layer(env):
    if not sql.column_exists(env.cr, "stock_valuation_layer", "account_value"):
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE stock_valuation_layer
            ADD COLUMN account_value float""",
        )
    if not sql.column_exists(env.cr, "stock_valuation_layer", "account_qty_at_date"):
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE stock_valuation_layer
            ADD COLUMN account_qty_at_date float""",
        )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE stock_valuation_layer svl0
        SET account_value = aml.debit - aml.credit
        FROM account_move_line aml
        INNER JOIN account_move am ON aml.move_id = am.id
        INNER JOIN stock_valuation_layer svl1 ON svl1.account_move_id = am.id
        INNER JOIN product_product pp ON pp.id = svl1.product_id
        WHERE svl0.id = svl1.id
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE stock_valuation_layer svl0
        SET account_qty_at_date = aml.quantity
        FROM account_move_line aml
        INNER JOIN account_move am ON aml.move_id = am.id
        INNER JOIN stock_valuation_layer svl1 ON svl1.account_move_id = am.id
        INNER JOIN product_product pp ON pp.id = svl1.product_id
        WHERE svl0.id = svl1.id
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    fill_stock_valuation_layer(env)
