# Copyright 2020 ForgeFlow S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import _, api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    stock_value = fields.Float("Inventory Value", compute="_compute_inventory_value")
    account_value = fields.Float("Accounting Value", compute="_compute_inventory_value")
    qty_at_date = fields.Float("Inventory Quantity", compute="_compute_inventory_value")
    account_qty_at_date = fields.Float(
        "Accounting Quantity", compute="_compute_inventory_value"
    )
    stock_fifo_real_time_aml_ids = fields.Many2many(
        "account.move.line", compute="_compute_inventory_value"
    )
    stock_valuation_layer_ids = fields.Many2many(
        "stock.valuation.layer", compute="_compute_inventory_value"
    )
    valuation_discrepancy = fields.Float(
        compute="_compute_inventory_value",
        search="_search_valuation_discrepancy",
    )
    qty_discrepancy = fields.Float(
        compute="_compute_inventory_value",
        search="_search_qty_discrepancy",
    )
    valuation = fields.Selection(
        related="product_tmpl_id.valuation", search="_search_valuation"
    )

    @api.model
    def _search_valuation(self, operator, value):
        domain = [
            "|",
            ("categ_id.property_valuation", operator, value),
            ("property_valuation", operator, value),
        ]
        products = self.env["product.product"].search(domain)
        if value:
            return [("id", "in", products.ids)]
        else:
            return [("id", "not in", products.ids)]

    @api.model
    def _search_qty_discrepancy(self, operator, value):
        products = self.env["product.product"].search([("type", "=", "product")])
        pp_list = []
        for pp in products:
            if pp.qty_at_date != pp.account_qty_at_date:
                pp_list.append(pp.id)
        return [("id", "in", pp_list)]

    @api.model
    def _search_valuation_discrepancy(self, operator, value):
        products = self.env["product.product"].search([("type", "=", "product")])
        pp_list = []
        for pp in products:
            if pp.stock_value != pp.account_value:
                pp_list.append(pp.id)
        return [("id", "in", pp_list)]

    def _compute_inventory_value(self):
        self.env["account.move.line"].check_access_rights("read")
        to_date = self.env.context.get("at_date", False)
        accounting_values = {}
        layer_values = {}
        # pylint: disable=E8103
        query = """
            SELECT aml.product_id, aml.account_id,
            sum(aml.balance), sum(quantity),
            array_agg(aml.id)
            FROM account_move_line AS aml
            INNER JOIN account_move AS am ON am.id = aml.move_id
            WHERE aml.product_id IN %%s
            AND am.state = 'posted'
            AND aml.company_id=%%s %s
            GROUP BY aml.product_id, aml.account_id"""
        params = (
            tuple(
                self._ids,
            ),
            self.env.company.id,
        )
        if to_date:
            # pylint: disable=sql-injection
            query = query % ("AND aml.date <= %s",)
            params = params + (to_date,)
        else:
            query = query % ("",)
        # pylint: disable=E8103
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        for row in res:
            accounting_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))
        # pylint: disable=E8103
        query = """
            SELECT DISTINCT ON ("product_id") product_id, sum(quantity),
            sum(value), array_agg(svl.id)
            FROM   "stock_valuation_layer" AS svl
            WHERE svl.product_id IN %%s
            AND svl.company_id=%%s %s
            GROUP BY product_id
            ORDER BY "product_id" DESC NULLS LAST
            """
        params = (
            tuple(
                self._ids,
            ),
            self.env.company.id,
        )
        if to_date:
            # pylint: disable=sql-injection
            query = query % ("AND svl.create_date <= %s",)
            params = params + (to_date,)
        else:
            query = query % ("",)
        # pylint: disable=E8103
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        aml_ids = self.env["account.move.line"]
        for row in res:
            layer_values[row[0]] = (row[1], row[2], list(row[3]))
        for product in self:
            # Retrieve the values from accounting
            # We cannot provide location-specific accounting valuation,
            # so better, leave the data empty in that case:
            if product.valuation == "real_time":
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
            else:
                product.account_value = 0.0
                product.account_qty_at_date = 0.0
                product.stock_fifo_real_time_aml_ids = []
            # Retrieve the values from inventory
            quantity, value, svl_ids = layer_values.get(product.id) or (0, 0, [])
            product.stock_value = value
            product.qty_at_date = quantity
            product.stock_valuation_layer_ids = self.env[
                "stock.valuation.layer"
            ].browse(svl_ids)
            if product.valuation == "real_time":
                product.valuation_discrepancy = (
                    product.stock_value - product.account_value
                )
                product.qty_discrepancy = (
                    product.qty_at_date - product.account_qty_at_date
                )
            else:
                product.valuation_discrepancy = 0.0
                product.qty_discrepancy = 0.0

    def action_view_amls(self):
        self.ensure_one()
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
                    self.stock_fifo_real_time_aml_ids.ids,
                )
            ],
            "views": [(tree_view_ref.id, "tree"), (form_view_ref.id, "form")],
        }
        return action

    def action_view_valuation_layers(self):
        self.ensure_one()
        tree_view_ref = self.env.ref("stock_account.stock_valuation_layer_tree")
        form_view_ref = self.env.ref("stock_account.stock_valuation_layer_form")
        action = {
            "name": _("Inventory Valuation"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "context": self.env.context,
            "res_model": "stock.valuation.layer",
            "domain": [
                (
                    "id",
                    "in",
                    self.stock_valuation_layer_ids.ids,
                )
            ],
            "views": [(tree_view_ref.id, "tree"), (form_view_ref.id, "form")],
        }
        return action
