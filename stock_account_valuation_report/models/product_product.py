# Copyright 2020 ForgeFlow S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.fields import Domain
from odoo.tools import float_compare


class ProductProduct(models.Model):
    _inherit = "product.product"

    stock_value = fields.Monetary(
        "Inventory Value",
        compute="_compute_inventory_value",
        currency_field="cost_currency_id",
    )
    account_value = fields.Monetary(
        "Accounting Value",
        compute="_compute_inventory_value",
        currency_field="cost_currency_id",
    )
    qty_at_date = fields.Float(
        "Inventory Quantity",
        compute="_compute_inventory_value",
        digits="Product Unit of Measure",
    )
    account_qty_at_date = fields.Float(
        "Accounting Quantity",
        compute="_compute_inventory_value",
        digits="Product Unit of Measure",
    )
    valuation_discrepancy = fields.Monetary(
        compute="_compute_inventory_value",
        search="_search_valuation_discrepancy",
        currency_field="cost_currency_id",
    )
    qty_discrepancy = fields.Float(
        compute="_compute_inventory_value",
        search="_search_qty_discrepancy",
        digits="Product Unit of Measure",
    )

    @api.model
    def _search_valuation_discrepancy(self, operator, value):
        return Domain("id", "in", self._get_discrepancy_product_ids())

    @api.model
    def _search_qty_discrepancy(self, operator, value):
        return Domain("id", "in", self._get_qty_discrepancy_product_ids())

    @api.model
    def _get_discrepancy_product_ids(self):
        """Return product IDs where stock and accounting values diverge."""
        to_date = self.env.context.get("at_date", False)
        company_id = self.env.company.id
        categories = self.env["product.category"].search(
            Domain("property_valuation", "=", "real_time")
        )
        company_default = self.env.company.account_stock_valuation_id
        categ_field = self.env["product.category"]._fields[
            "property_stock_valuation_account_id"
        ]
        categ_accounts = {}
        for c in categories:
            acc = (
                c.property_stock_valuation_account_id
                or categ_field.get_company_dependent_fallback(c)
                or company_default
            )
            if acc:
                categ_accounts[c.id] = acc.id
        if not categ_accounts:
            return []
        account_ids = list(set(categ_accounts.values()))
        # pylint: disable=E8103
        self.env.cr.execute(
            """
            SELECT pp.id, pt.categ_id
            FROM product_product pp
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pt.categ_id = ANY(%s)
            """,
            (list(categ_accounts.keys()),),
        )
        rows = self.env.cr.fetchall()
        if not rows:
            return []
        product_to_account = {row[0]: categ_accounts[row[1]] for row in rows}
        product_ids = list(product_to_account.keys())
        date_param = (to_date,) if to_date else ()
        aml_date_clause = "AND aml.date <= %s" if to_date else ""
        precision_kwargs = {"precision_rounding": self.env.company.currency_id.rounding}
        move_domain = (
            Domain("product_id", "in", product_ids)
            & Domain("company_id", "=", company_id)
            & Domain("state", "=", "done")
        )
        if to_date:
            move_domain &= Domain("date", "<=", to_date)
        stock_vals = {}
        for move in self.env["stock.move"].search(move_domain):
            pid = move.product_id.id
            stock_vals[pid] = stock_vals.get(pid, 0.0) + move.remaining_value
        self.env["account.move.line"].flush_model()
        # pylint: disable=E8103
        self.env.cr.execute(
            f"""
            SELECT aml.product_id, SUM(aml.balance)
            FROM account_move_line aml
            WHERE aml.parent_state = 'posted'
            AND aml.company_id = %s
            AND aml.product_id = ANY(%s)
            AND aml.account_id = ANY(%s)
            {aml_date_clause}
            GROUP BY aml.product_id
            """,
            (company_id, product_ids, account_ids) + date_param,
        )
        acct_vals = dict(self.env.cr.fetchall())
        return [
            pid
            for pid in product_ids
            if float_compare(
                stock_vals.get(pid, 0.0),
                acct_vals.get(pid, 0.0),
                **precision_kwargs,
            )
            != 0
        ]

    @api.model
    def _get_qty_discrepancy_product_ids(self):
        """Return product IDs where stock and accounting quantities diverge."""
        to_date = self.env.context.get("at_date", False)
        company_id = self.env.company.id
        categories = self.env["product.category"].search(
            Domain("property_valuation", "=", "real_time")
        )
        company_default = self.env.company.account_stock_valuation_id
        categ_field = self.env["product.category"]._fields[
            "property_stock_valuation_account_id"
        ]
        categ_accounts = {}
        for c in categories:
            acc = (
                c.property_stock_valuation_account_id
                or categ_field.get_company_dependent_fallback(c)
                or company_default
            )
            if acc:
                categ_accounts[c.id] = acc.id
        if not categ_accounts:
            return []
        account_ids = list(set(categ_accounts.values()))
        # pylint: disable=E8103
        self.env.cr.execute(
            """
            SELECT pp.id, pt.categ_id
            FROM product_product pp
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pt.categ_id = ANY(%s)
            """,
            (list(categ_accounts.keys()),),
        )
        rows = self.env.cr.fetchall()
        if not rows:
            return []
        product_ids = [row[0] for row in rows]
        date_param = (to_date,) if to_date else ()
        aml_date_clause = "AND aml.date <= %s" if to_date else ""
        move_domain = (
            Domain("product_id", "in", product_ids)
            & Domain("company_id", "=", company_id)
            & Domain("state", "=", "done")
        )
        if to_date:
            move_domain &= Domain("date", "<=", to_date)
        stock_qtys = {}
        for move in self.env["stock.move"].search(move_domain):
            pid = move.product_id.id
            stock_qtys[pid] = stock_qtys.get(pid, 0.0) + move.remaining_qty
        self.env["account.move.line"].flush_model()
        # pylint: disable=E8103
        self.env.cr.execute(
            f"""
            SELECT aml.product_id,
            SUM(
                CASE WHEN aml.display_type IN ('product', 'cogs')
                THEN SIGN(aml.balance) * aml.quantity
                ELSE 0 END
            )
            FROM account_move_line aml
            WHERE aml.parent_state = 'posted'
            AND aml.company_id = %s
            AND aml.product_id = ANY(%s)
            AND aml.account_id = ANY(%s)
            {aml_date_clause}
            GROUP BY aml.product_id
            """,
            (company_id, product_ids, account_ids) + date_param,
        )
        acct_qtys = dict(self.env.cr.fetchall())
        products_by_id = {p.id: p for p in self.browse(product_ids)}
        return [
            pid
            for pid in product_ids
            if float_compare(
                stock_qtys.get(pid, 0.0),
                acct_qtys.get(pid, 0.0),
                precision_rounding=products_by_id[pid].uom_id.rounding,
            )
            != 0
        ]

    def _get_valuation_aml_ids(self, product, to_date):
        valuation_account_id = product._get_product_accounts()["stock_valuation"].id
        if not valuation_account_id:
            return []
        self.env["account.move.line"].flush_model()
        # pylint: disable=E8103
        query = """
            SELECT array_agg(aml.id)
            FROM account_move_line AS aml
            WHERE aml.product_id = %s
            AND aml.parent_state = 'posted'
            AND aml.company_id = %s
            AND aml.account_id = %s
            {where_date_clause}
        """
        params = (product.id, self.env.company.id, valuation_account_id)
        where_date_clause = "AND aml.date <= %s" if to_date else ""
        query = query.format(where_date_clause=where_date_clause)
        if to_date:
            params = params + (to_date,)
        self.env.cr.execute(query, params=params)
        row = self.env.cr.fetchone()
        return list(row[0]) if row and row[0] else []

    def _compute_inventory_value(self):
        self.env["account.move.line"].check_access("read")
        to_date = self.env.context.get("at_date", False)
        # 1) ACCOUNTING VALUES — restrict to valuation accounts only
        # Use _get_product_accounts() for the full 3-level fallback on account lookup
        product_valuation_account = {}
        for product in self:
            if product.valuation == "real_time":
                acc_id = product._get_product_accounts()["stock_valuation"].id
                if acc_id:
                    product_valuation_account[product.id] = acc_id
        valuation_account_ids = set(product_valuation_account.values())

        accounting_values = {}
        accounting_qtys = {}
        if valuation_account_ids:
            self.env["account.move.line"].flush_model()
            # pylint: disable=E8103
            query = """
                SELECT aml.product_id, aml.account_id,
                sum(aml.balance),
                sum(
                    CASE WHEN aml.display_type IN ('product', 'cogs')
                    THEN SIGN(aml.balance) * aml.quantity
                    ELSE 0 END
                )
                FROM account_move_line AS aml
                WHERE aml.product_id IN %s
                AND aml.parent_state = 'posted'
                AND aml.company_id = %s
                AND aml.account_id IN %s
                {where_date_clause}
                GROUP BY aml.product_id, aml.account_id
            """
            params = (
                tuple(self.ids),
                self.env.company.id,
                tuple(valuation_account_ids),
            )
            where_date_clause = "AND aml.date <= %s" if to_date else ""
            query = query.format(where_date_clause=where_date_clause)
            if to_date:
                params = params + (to_date,)
            self.env.cr.execute(query, params=params)
            for row in self.env.cr.fetchall():
                accounting_values[(row[0], row[1])] = row[2]
                accounting_qtys[(row[0], row[1])] = row[3]
        # 2) INVENTORY VALUES
        move_domain = (
            Domain("product_id", "in", self.ids)
            & Domain("company_id", "=", self.env.company.id)
            & Domain("state", "=", "done")
        )
        if to_date:
            move_domain &= Domain("date", "<=", to_date)
        moves = self.env["stock.move"].search(move_domain)
        move_values = {}
        for move in moves:
            pid = move.product_id.id
            move_values[pid] = move_values.get(pid, {"qty": 0, "value": 0})
            move_values[pid]["qty"] += move.remaining_qty
            move_values[pid]["value"] += move.remaining_value
        for product in self:
            if product.valuation == "real_time":
                valuation_account_id = product_valuation_account.get(product.id)
                product.account_value = accounting_values.get(
                    (product.id, valuation_account_id), 0
                )
                product.account_qty_at_date = accounting_qtys.get(
                    (product.id, valuation_account_id), 0
                )
            else:
                product.account_value = 0
                product.account_qty_at_date = 0
            move_data = move_values.get(product.id, {})
            product.qty_at_date = move_data.get("qty", 0)
            product.stock_value = move_data.get("value", 0)
            if product.valuation == "real_time":
                product.valuation_discrepancy = (
                    product.stock_value - product.account_value
                )
                product.qty_discrepancy = (
                    product.qty_at_date - product.account_qty_at_date
                )
            else:
                product.valuation_discrepancy = 0
                product.qty_discrepancy = 0

    def action_view_amls(self):
        self.ensure_one()
        to_date = self.env.context.get("at_date", False)
        aml_ids = self._get_valuation_aml_ids(self, to_date)
        list_view_ref = self.env.ref("account.view_move_line_tree")
        form_view_ref = self.env.ref("account.view_move_line_form")
        return {
            "name": self.env._("Accounting Valuation at date"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "list,form",
            "context": self.env.context,
            "res_model": "account.move.line",
            "domain": Domain("id", "in", aml_ids),
            "views": [(list_view_ref.id, "list"), (form_view_ref.id, "form")],
        }

    def _get_move_ids(self, product_ids, to_date):
        # pylint: disable=E8103
        query = """
            SELECT id FROM stock_move
            WHERE state = 'done' AND company_id = %s AND product_id = ANY(%s)
            {where_date_clause}
        """
        params = (self.env.company.id, product_ids)
        date_clause = "AND date <= %s" if to_date else ""
        query = query.format(where_date_clause=date_clause)
        if to_date:
            params = params + (to_date,)
        self.env.cr.execute(query, params=params)
        return [row[0] for row in self.env.cr.fetchall()]

    def action_view_valuation_layers(self):
        to_date = self.env.context.get("at_date", False)
        move_ids = self._get_move_ids(self.ids, to_date)
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_account.stock_valuation_layer_report_action"
        )
        action["domain"] = Domain("id", "in", move_ids)
        action["context"] = {}
        return action

    def action_view_valuation_moves(self):
        self.ensure_one()
        to_date = self.env.context.get("at_date", False)
        move_ids = self._get_move_ids(self.ids, to_date)
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_action")
        action["domain"] = Domain("id", "in", move_ids)
        return action
