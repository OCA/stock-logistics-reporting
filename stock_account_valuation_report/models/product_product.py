# -*- coding: utf-8 -*-
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
#   (<https://www.eficent.com>)
# Copyright 2018 Aleph Objects, Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, _


class ProductProduct(models.Model):
    _inherit = "product.product"

    stock_value = fields.Float(
        "Inventory Value", compute="_compute_inventory_value"
    )
    account_value = fields.Float(
        "Accounting Value", compute="_compute_inventory_value"
    )
    qty_at_date = fields.Float(
        "Inventory Quantity", compute="_compute_inventory_value"
    )
    account_qty_at_date = fields.Float(
        "Accounting Quantity", compute="_compute_inventory_value"
    )
    stock_fifo_real_time_aml_ids = fields.Many2many(
        "account.move.line", compute="_compute_inventory_value"
    )

    def _compute_inventory_value(self):
        self.env["account.move.line"].check_access_rights("read")
        location = self.env.context.get("location", False)
        accounting_values = {}
        if not location:
            # pylint: disable=E8103
            query = """
                SELECT aml.product_id, aml.account_id,
                sum(aml.debit) - sum(aml.credit), sum(quantity),
                array_agg(aml.id)
                FROM account_move_line AS aml
                WHERE aml.product_id IN %%s
                AND aml.company_id=%%s %s
                GROUP BY aml.product_id, aml.account_id"""
            params = (tuple(self._ids,), self.env.user.company_id.id)
            query = query % ("",)
            self.env.cr.execute(query, params=params)
            res = self.env.cr.fetchall()
            for row in res:
                accounting_values[(row[0], row[1])] = (
                    row[2],
                    row[3],
                    list(row[4]),
                )
        quantities_dict = self._compute_quantities_dict(
            self._context.get("lot_id"),
            self._context.get("owner_id"),
            self._context.get("package_id"),
            self._context.get("from_date"),
            self._context.get("to_date"),
        )

        # pylint: disable=E8103
        self.env.cr.execute(
            """
            SELECT MAX(id) FROM product_product;
        """
        )
        quant_data = {
            key: [0, 0] for key in range(1, self.env.cr.fetchone()[0] + 1)
        }
        # Retrieve the values from inventory for real cost
        # pylint: disable=E8103
        query = """
            SELECT pp.id as x_product_id, sum(qty) as x_quantity,
            sum(cost)*sum(qty) as x_total_value
            FROM stock_quant sq
            INNER JOIN stock_location sl ON sq.location_id = sl.id
            INNER JOIN product_product pp ON sq.product_id = pp.id
            INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
            WHERE sl.usage = 'internal'
            AND sq.company_id = %%s %s
            GROUP BY pp.id
        """
        params = (self.env.user.company_id.id, )
        query = query % ("",)
        self.env.cr.execute(query, params=params)
        for x_product_id, x_quantity, x_total_value in self.env.cr.fetchall():
            quant_data[x_product_id][0] = x_quantity
            quant_data[x_product_id][1] = x_total_value

        for product in self.filtered(lambda p: p.type == "product"):
            qty_available = quantities_dict[product.id]["qty_available"]
            # Retrieve the values from accounting
            # We cannot provide location-specific accounting valuation,
            # so better, leave the data empty in that case

            # if product is not "real time" accounting is not relevant
            if product.valuation == "real_time" and not location:
                valuation_account_id = (
                    product.categ_id.property_stock_valuation_account_id.id
                )
                value, quantity, aml_ids = accounting_values.get(
                    (product.id, valuation_account_id)
                ) or (0, 0, [])
                product.account_value = value
                product.account_qty_at_date = quantity
                product.stock_fifo_real_time_aml_ids = self.env[
                    "account.move.line"
                ].browse(aml_ids)
            # if no quant it is just zero
            if quant_data.get(product.id, False):
                product.qty_at_date = quant_data[product.id][0]
                product.stock_value = quant_data[product.id][1]
            else:
                product.qty_at_date = 0.0
                product.stock_value = 0.0
            if product.cost_method in ["standard", "average"]:
                price_used = product.standard_price
                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available

    def action_view_amls(self):
        self.ensure_one()
        to_date = self.env.context.get("to_date")
        tree_view_ref = self.env.ref("account.view_move_line_tree")
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
        tree_view_ref = self.env.ref("stock.view_move_tree")
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
