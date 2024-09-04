# Copyright 2021 ForgeFlow S.L.
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WizardStockDiscrepancyAdjustment(models.TransientModel):

    _name = "wizard.stock.discrepancy.adjustment"
    _description = "Wizard Stock Discrepancy Adjustment"

    def _get_default_stock_journal(self):
        return self.env["account.journal"].search(
            [
                ("type", "=", "general"),
                ("company_id", "=", self.env.user.company_id.id),
            ],
            limit=1,
        )

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        domain=[("type", "=", "general")],
        default=_get_default_stock_journal,
    )
    increase_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Increase account",
        domain=[("deprecated", "=", False)],
        required=False,
    )
    decrease_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Decrease account",
        domain=[("deprecated", "=", False)],
        required=False,
    )
    to_date = fields.Datetime(
        string="To date",
        required=False,
        default=fields.Datetime.now(),
    )
    product_ids = fields.Many2many(
        comodel_name="product.product",
        relation="wizard_discrepancy_product_product_rel",
        column1="wizard_id",
        column2="product_id",
        string="Product",
    )
    selected_product_ids = fields.Many2many(
        comodel_name="product.product",
        relation="wizard_discrepancy_selected_product_product_rel",
        column1="wizard_id",
        column2="product_id",
        string="Product",
    )

    @api.model
    def default_get(self, fields_list):
        values = super(WizardStockDiscrepancyAdjustment, self).default_get(fields_list)
        product_discrepancy_model = self.env["product.discrepancy"]
        if self.env.context.get("active_model", False) == "product.discrepancy":
            records = product_discrepancy_model.browse(
                self.env.context.get("active_ids")
            )
            values["selected_product_ids"] = records.mapped("product_id").ids
            values["to_date"] = records.mapped("to_date_valuation")[0]
        return values

    @api.onchange(
        "to_date",
        "selected_product_ids",
    )
    def _onchange_at_date(self):
        product_model = self.env["product.product"]
        if self.selected_product_ids:
            self.product_ids = self.selected_product_ids.ids or [(6, 0, [])]
        elif self.to_date:
            products = product_model.with_context(
                to_date=self.to_date, target_move="posted"
            ).search([("valuation_discrepancy", "!=", 0.0)])
            self.product_ids = products.ids or [(6, 0, [])]

    def action_create_adjustment(self):
        move_model = self.env["account.move"]
        product_model = self.env["product.product"]
        moves_created = move_model.browse()
        if self.product_ids or self.selected_product_ids:
            products_with_discrepancy = product_model.with_context(
                to_date=self.to_date
            ).browse(self.product_ids.ids or self.selected_product_ids.ids)
            for product in products_with_discrepancy:
                move_data = {
                    "journal_id": self.journal_id.id,
                    "date": self.to_date,
                    "ref": _("Adjust for Stock Valuation Discrepancy"),
                }
                valuation_account = product.product_tmpl_id._get_product_accounts()[
                    "stock_valuation"
                ]
                if not valuation_account:
                    raise UserError(
                        _("Product %s doesn't " "have stock valuation account assigned")
                        % (product.display_name)
                    )
                move_data["line_ids"] = [
                    (
                        0,
                        0,
                        {
                            "account_id": valuation_account.id,
                            "product_id": product.id,
                            "quantity": product.qty_discrepancy,
                            "credit": product.valuation_discrepancy < 0
                            and abs(product.valuation_discrepancy)
                            or 0.0,
                            "debit": product.valuation_discrepancy > 0
                            and product.valuation_discrepancy
                            or 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": product.valuation_discrepancy < 0
                            and self.increase_account_id.id
                            or self.decrease_account_id.id,
                            "product_id": product.id,
                            "quantity": product.qty_discrepancy,
                            "credit": product.valuation_discrepancy > 0
                            and product.valuation_discrepancy
                            or 0.0,
                            "debit": product.valuation_discrepancy < 0
                            and abs(product.valuation_discrepancy)
                            or 0.0,
                        },
                    ),
                ]
                move = move_model.create(move_data)
                move.action_post()
                moves_created |= move
            action = self.env.ref("account.action_move_journal_line").read()[0]
            action["domain"] = [("id", "in", moves_created.ids)]
            return action
        return {"type": "ir.actions.act_window_close"}
