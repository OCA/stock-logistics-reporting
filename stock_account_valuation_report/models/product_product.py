# Copyright 2018-2021 ForgeFlow S.L.
# Copyright 2018 Aleph Objects, Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _
from odoo.exceptions import UserError

import operator

ops = {
    "=": operator.eq,
    "!=": operator.ne,
    "<=": operator.le,
    ">=": operator.ge,
    ">": operator.gt,
    "<": operator.lt,
}


class ProductProduct(models.Model):
    _inherit = "product.product"

    stock_value = fields.Float("Inventory Value",
                               compute="_compute_inventory_value")
    account_value = fields.Float("Accounting Value",
                                 compute="_compute_inventory_value")
    qty_at_date = fields.Float("Inventory Quantity",
                               compute="_compute_inventory_value")
    account_qty_at_date = fields.Float(
        "Accounting Quantity", compute="_compute_inventory_value"
    )
    stock_fifo_real_time_aml_ids = fields.Many2many(
        "account.move.line", compute="_compute_inventory_value"
    )
    stock_fifo_manual_move_ids = fields.Many2many(
        "stock.move", compute="_compute_inventory_value"
    )
    valuation_discrepancy = fields.Float(
        string="Valuation discrepancy",
        compute="_compute_inventory_value",
        search="_search_valuation_discrepancy",
    )
    qty_discrepancy = fields.Float(
        string="Quantity discrepancy",
        compute="_compute_inventory_value",
    )

    def _compute_inventory_value(self):
        stock_move = self.env["stock.move"]
        self.env["account.move.line"].check_access_rights("read")
        to_date = self.env.context.get("to_date", False)
        location = self.env.context.get("location", False)
        target_move = self.env.context.get("target_move", False)
        accounting_values = {}
        if not location:
            # pylint: disable=E8103
            query = (
                """
                SELECT aml.product_id, aml.account_id,
                sum(aml.debit) - sum(aml.credit), sum(quantity),
                array_agg(aml.id)
                FROM account_move_line AS aml
                INNER JOIN account_move as am on am.id = aml.move_id
                WHERE aml.product_id IN %%s
                AND aml.company_id=%%s %s"""
                + (target_move == "posted"
                   and " AND am.state = 'posted' " or "")
                + """ GROUP BY aml.product_id, aml.account_id """
            )
            params = (
                tuple(
                    self._ids,
                ),
                self.env.user.company_id.id,
            )
            if to_date:
                # pylint: disable=sql-injection
                query = query % ("AND aml.date <= %s",)
                params = params + (to_date,)
            else:
                query = query % ("",)
            self.env.cr.execute(query, params=params)
            res = self.env.cr.fetchall()
            for row in res:
                accounting_values[(row[0], row[1])] = (
                    row[2], row[3], list(row[4])
                )
        stock_move_domain = [
            ("product_id", "in", self._ids),
            ("date", "<=", to_date),
        ] + stock_move._get_all_base_domain()
        moves = stock_move.search(stock_move_domain)
        history = {}
        if to_date:
            query = """
                SELECT DISTINCT ON ("product_id") product_id, cost
                FROM   "product_price_history"
                WHERE datetime <= %s::date
                AND product_id IN %s
                ORDER  BY "product_id", "datetime" DESC NULLS LAST
                """
            args = (to_date, tuple(self._ids))
            self.env.cr.execute(query, args)
            for row in self.env.cr.dictfetchall():
                history.update({row["product_id"]: row["cost"]})
        quantities_dict = self._compute_quantities_dict(
            self._context.get("lot_id"),
            self._context.get("owner_id"),
            self._context.get("package_id"),
            self._context.get("from_date"),
            self._context.get("to_date"),
        )
        computed_data = {}
        for product in self:
            computed_data.setdefault(
                product.id,
                {
                    "account_value": 0.0,
                    "account_qty_at_date": 0.0,
                    "stock_fifo_real_time_aml_ids": [],
                    "stock_value": 0.0,
                    "qty_at_date": 0.0,
                    "stock_fifo_manual_move_ids": [],
                    "valuation_discrepancy": 0.0,
                    "qty_discrepancy": 0.0,
                },
            )
            qty_available = quantities_dict[product.id]["qty_available"]
            # Retrieve the values from accounting
            # We cannot provide location-specific accounting valuation,
            # so better, leave the data empty in that case:
            if product.valuation == "real_time" and not location:
                valuation_account_id = (
                    product.categ_id.property_stock_valuation_account_id.id
                )
                value, quantity, aml_ids = accounting_values.get(
                    (product.id, valuation_account_id)
                ) or (0, 0, [])
                computed_data[product.id]["account_value"] = value
                computed_data[product.id]["account_qty_at_date"] = quantity
                computed_data[product.id]["stock_fifo_real_time_aml_ids"] = \
                    self.env[
                    "account.move.line"
                ].browse(aml_ids)
            # Retrieve the values from inventory
            if product.cost_method in ["standard", "average"]:
                price_used = product.standard_price
                if to_date:
                    price_used = history.get(product.id, 0)
                computed_data[product.id]["stock_value"] = \
                    price_used * qty_available
                computed_data[product.id]["qty_at_date"] = qty_available
            elif product.cost_method == "fifo":
                if to_date:
                    if product.product_tmpl_id.valuation == "manual_periodic":
                        computed_data[product.id]["stock_value"] = sum(
                            moves.mapped("value")
                        )
                        computed_data[product.id]["qty_at_date"] = \
                            qty_available
                        computed_data[product.id][
                            "stock_fifo_manual_move_ids"
                        ] = stock_move.browse(moves.ids)
                else:
                    (
                        computed_data[product.id]["stock_value"],
                        moves,
                    ) = product._sum_remaining_values()
                    computed_data[product.id]["qty_at_date"] = qty_available
                    computed_data[product.id]["stock_fifo_manual_move_ids"] = \
                        moves
            if product.categ_id.property_valuation == "real_time":
                computed_data[product.id]["valuation_discrepancy"] = (
                    computed_data[product.id]["stock_value"]
                    - computed_data[product.id]["account_value"]
                )
                computed_data[product.id]["qty_discrepancy"] = (
                    computed_data[product.id]["qty_at_date"]
                    - computed_data[product.id]["account_qty_at_date"]
                )
            for key in computed_data[product.id].keys():
                product[key] = computed_data[product.id].get(key)
        return computed_data

    @api.multi
    def _search_valuation_discrepancy(self, search_operator, value):
        if search_operator not in ops.keys():
            raise UserError(
                _("Search operator %s not implemented for value %s")
                % (search_operator, value)
            )
        products = self.search(
            [
                ("active", "=", True),
                ("categ_id.property_valuation", "=", "real_time"),
            ]
        )
        found_ids = []
        if products:
            computed_data = products._compute_inventory_value()
            for product in products:
                accounting_v = computed_data.get(product.id, {}).get(
                    "account_value"
                )
                inventory_v = computed_data.get(product.id, {}).get(
                    "stock_value"
                )
                valuation_discrepancy = inventory_v - accounting_v
                if ops[search_operator](valuation_discrepancy, value):
                    found_ids.append(product.id)
        return [("id", "in", found_ids)]

    def action_view_amls(self):
        self.ensure_one()
        to_date = self.env.context.get("to_date")
        tree_view_ref = self.env.ref("stock_account.view_stock_account_aml")
        form_view_ref = self.env.ref("account.view_move_line_form")
        action = {
            "name": _("Accounting Valuation at date"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "context": self.env.context,
            "res_model": "account.move.line",
            "domain": [
                (
                    "id",
                    "in",
                    self.with_context(
                        to_date=to_date
                    ).stock_fifo_real_time_aml_ids.ids,
                )
            ],
            "views": [(tree_view_ref.id, "tree"), (form_view_ref.id, "form")],
        }
        return action

    def action_view_stock_moves(self):
        self.ensure_one()
        to_date = self.env.context.get("to_date")
        tree_view_ref = self.env.ref(
            "stock_account.view_move_tree_valuation_at_date"
        )
        form_view_ref = self.env.ref("stock.view_move_form")
        action = {
            "name": _("Inventory Valuation"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "context": self.env.context,
            "res_model": "stock.move",
            "domain": [
                (
                    "id",
                    "in",
                    self.with_context(
                        to_date=to_date
                    ).stock_fifo_manual_move_ids.ids,
                )
            ],
            "views": [(tree_view_ref.id, "tree"), (form_view_ref.id, "form")],
        }
        return action
