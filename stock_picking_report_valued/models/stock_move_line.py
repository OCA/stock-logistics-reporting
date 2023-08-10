# Copyright 2014-2018 Tecnativa - Pedro M. Baeza
# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2018 Tecnativa - Luis M. Ontalba
# Copyright 2016-2022 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import float_compare


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sale_line = fields.Many2one(
        related="move_id.sale_line_id", readonly=True, string="Related order line"
    )
    currency_id = fields.Many2one(
        related="sale_line.currency_id", readonly=True, string="Sale Currency"
    )
    sale_tax_id = fields.Many2many(
        related="sale_line.tax_id", readonly=True, string="Sale Tax"
    )
    sale_price_unit = fields.Monetary(
        compute="_compute_sale_order_line_fields",
        compute_sudo=True,
    )
    sale_discount = fields.Float(
        related="sale_line.discount", readonly=True, string="Sale discount (%)"
    )
    sale_tax_description = fields.Char(
        compute="_compute_sale_order_line_fields",
        string="Tax Description",
        compute_sudo=True,  # See explanation for sudo in compute method
    )
    sale_price_subtotal = fields.Monetary(
        compute="_compute_sale_order_line_fields",
        string="Price subtotal",
        compute_sudo=True,
    )
    sale_price_tax = fields.Float(
        compute="_compute_sale_order_line_fields", string="Taxes", compute_sudo=True
    )
    sale_price_total = fields.Monetary(
        compute="_compute_sale_order_line_fields", string="Total", compute_sudo=True
    )

    def _get_report_valued_quantity(self):
        return self.qty_done or self.product_qty

    def _compute_sale_order_line_fields(self):
        """This is computed with sudo for avoiding problems if you don't have
        access to sales orders (stricter warehouse users, inter-company
        records...).
        """
        self.sale_tax_description = False
        self.sale_price_subtotal = False
        self.sale_price_tax = False
        self.sale_price_total = False
        self.sale_price_unit = False
        for line in self:
            valued_line = line.sale_line
            if not valued_line:
                continue
            quantity = line._get_report_valued_quantity()
            sale_line_uom = valued_line.product_uom
            different_uom = valued_line.product_uom != line.product_uom_id
            # If order line quantity don't match with move line quantity compute values
            different_qty = float_compare(
                quantity,
                line.sale_line.product_uom_qty,
                precision_rounding=line.product_uom_id.rounding,
            )
            if different_uom or different_qty:
                # Force read to cache M2M field for get values with _convert_to_write
                line.sale_line.mapped("tax_id")
                # Create virtual sale line with stock move line quantity
                sol_vals = line.sale_line._convert_to_write(line.sale_line._cache)
                valued_line = line.sale_line.new(sol_vals)
                valued_line.product_uom_qty = quantity
            if different_qty:
                # Force original price unit to avoid pricelist recomputed (not needed)
                valued_line.price_unit = line.sale_line.price_unit
            if different_uom:
                valued_line.price_unit = sale_line_uom._compute_price(
                    valued_line.price_unit, line.product_uom_id
                )
            line.update(
                {
                    "sale_tax_description": ", ".join(
                        t.name or t.description for t in line.sale_tax_id
                    ),
                    "sale_price_subtotal": valued_line.price_subtotal,
                    "sale_price_tax": valued_line.price_tax,
                    "sale_price_total": valued_line.price_total,
                    "sale_price_unit": valued_line.price_unit,
                }
            )
