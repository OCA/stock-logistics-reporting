# Copyright 2021 ForgeFlow S.L.
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WizardStockDiscrepancyAdjustment(models.TransientModel):
    _name = "wizard.stock.discrepancy.adjustment"
    _description = "Wizard Stock Discrepancy Adjustment"

    product_selection_ids = fields.One2many(
        comodel_name="wizard.stock.discrepancy.adjustment.line",
        inverse_name="wizard_id",
        string="Selected Products",
    )
    single_journal_entry = fields.Boolean()

    def _get_default_stock_journal(self):
        return self.env["account.journal"].search(
            [
                ("type", "=", "general"),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        readonly=True,
        change_default=True,
        default=lambda self: self.env.company,
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
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get("active_model", False) != "product.product":
            raise UserError(_("Bad context propagation"))
        products = self.env["product.product"].browse(
            self.env.context.get("active_ids")
        )
        values["product_selection_ids"] = [
            (0, 0, {"product_id": product.id}) for product in products
        ]
        values["to_date"] = self.env.context.get("at_date", fields.Datetime.now())
        return values

    def _prepare_product_vals(self, product):
        """Prepare the product line values for the valuation discrepancy.

        Args:
            product: The product.product record

        Returns:
            list: A list containing the line values for the product side of the entry
        """
        valuation_account = product.product_tmpl_id._get_product_accounts()[
            "stock_valuation"
        ]
        if not valuation_account:
            raise UserError(
                self.env._("Product %s doesn't have stock valuation account assigned")
                % product.display_name
            )
        return [
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
            )
        ]

    def _prepare_counterpart_vals(self, product):
        """Prepare the counterpart line values for the valuation discrepancy.

        Args:
            product: The product.product record

        Returns:
            list: A list containing the line values
            for the counterpart side of the entry
        """
        return [
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
            )
        ]

    def _prepare_debit_credit_lines(self, product):
        """Prepare the debit and credit lines for a product's valuation discrepancy.

        Args:
            product: The product.product record

        Returns:
            list: A list of dicts containing the line data
        """
        return self._prepare_product_vals(product) + self._prepare_counterpart_vals(
            product
        )

    def _prepare_single_move_vals(self):
        """Prepare the move values for the adjustment entry for single journal entry.

        Returns:
            dict: The values for creating the adjustment move
        """
        return {
            "journal_id": self.journal_id.id,
            "date": fields.Date.context_today(self, self.to_date),
            "ref": _("Adjust for Stock Valuation Discrepancy"),
            "line_ids": [],
        }

    def _prepare_product_move_vals(self):
        """Prepare the move values for the adjustment entry for product journal entry.

        Returns:
            dict: The values for creating the adjustment move
        """
        return self._prepare_single_move_vals()

    def action_create_adjustment(self):
        move_model = self.env["account.move"]
        product_model = self.env["product.product"]
        moves_created = move_model.browse()
        if self.single_journal_entry:
            move_data = self._prepare_single_move_vals()

        if self.product_selection_ids:
            products_with_discrepancy = product_model.with_context(
                to_date=self.to_date
            ).browse(self.product_selection_ids.mapped("product_id").ids)

            for product in products_with_discrepancy:
                if not product._adjustment_needed():
                    continue
                account_move_lines = self._prepare_debit_credit_lines(product)

                # If single_journal_entry is True, append line items to move_data
                if self.single_journal_entry:
                    move_data["line_ids"].extend(account_move_lines)
                else:
                    # Create individual move for each product
                    move = move_model.create(
                        {
                            **self._prepare_product_move_vals(),
                            "line_ids": account_move_lines,
                        }
                    )
                    move.action_post()
                    moves_created |= move

            # If single_journal_entry is True, create one move with all lines
            if self.single_journal_entry:
                move = move_model.create(move_data)
                move.action_post()
                moves_created |= move

            action = self.env.ref("account.action_move_journal_line").read()[0]
            action["domain"] = [("id", "in", moves_created.ids)]
            return action

        return {"type": "ir.actions.act_window_close"}


class WizardSelectedProduct(models.TransientModel):
    _name = "wizard.stock.discrepancy.adjustment.line"
    _description = "Selected Product for Wizard"

    wizard_id = fields.Many2one(
        comodel_name="wizard.stock.discrepancy.adjustment",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
    )
    stock_value = fields.Float("Inventory Value", related="product_id.stock_value")
    account_value = fields.Float("Accounting Value", related="product_id.account_value")
    qty_at_date = fields.Float("Inventory Quantity", related="product_id.qty_at_date")
    account_qty_at_date = fields.Float(
        "Accounting Quantity", related="product_id.account_qty_at_date"
    )
    qty_discrepancy = fields.Float(related="product_id.qty_discrepancy")
    valuation_discrepancy = fields.Float(related="product_id.valuation_discrepancy")
