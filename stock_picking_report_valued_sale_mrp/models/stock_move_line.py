# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    phantom_product_id = fields.Many2one(
        comodel_name="product.product",
        compute="_compute_phantom_product_id",
        compute_sudo=True,
        string="Product Kit",
        readonly=True,
    )
    phantom_line = fields.Boolean(
        compute="_compute_sale_order_line_fields",
        compute_sudo=True,
    )
    phantom_delivered_qty = fields.Float(
        compute="_compute_sale_order_line_fields",
        compute_sudo=True,
    )

    @api.depends("sale_line")
    def _compute_phantom_product_id(self):
        """Relate every line with its kit product"""
        self.phantom_product_id = False
        for line in self.filtered(
            lambda x: x.sale_line
            and x.sale_line.product_id.get_components()
            and x.sale_line.product_id.ids != x.sale_line.product_id.get_components()
        ):
            line.phantom_product_id = line.sale_line.product_id

    def _compute_sale_order_line_fields(self):
        """For kits we only want to store the value in one of the move lines to
        avoid duplicate the amounts. We also need to recompute the total
        amounts according to the corresponding delivered kits"""
        res = super()._compute_sale_order_line_fields()
        pickings = self.mapped("picking_id")
        pickings.move_line_ids.update(
            {"phantom_line": False, "phantom_delivered_qty": 0.0}
        )
        for picking in pickings:
            self.filtered(
                lambda x: x.picking_id == picking
            )._compute_sale_order_line_fields_by_picking()
        return res

    def _compute_sale_order_line_fields_by_picking(self):
        """We want to compute the lines value by picking to avoid mixing lines
        if they weren't shipped altogether.
        """
        kit_lines = self.filtered("phantom_product_id")
        for sale_line in kit_lines.mapped("sale_line"):
            move_lines = kit_lines.filtered(lambda x: x.sale_line == sale_line)
            # Deduce the kit quantity from the first component in the picking.
            # If the the kit is partially delivered, this could lead to an
            # unacurate value.
            phantom_line = move_lines[:1]
            if not phantom_line:
                continue
            price_unit = (
                sale_line.price_subtotal / sale_line.product_uom_qty
                if sale_line.product_uom_qty
                else sale_line.price_reduce
            )
            # Compute how many kits were delivered from the components and
            # the original demand. Note that if the qty is edited in the sale
            # order this could lead to inconsitencies.
            components_per_kit = phantom_line.move_id._get_components_per_kit()
            phantom_line_qty_done = sum(
                move_lines.filtered(
                    lambda x: x.product_id == phantom_line.product_id
                ).mapped("qty_done")
            )
            quantity = phantom_line_qty_done / components_per_kit
            taxes = phantom_line.sale_tax_id.compute_all(
                price_unit=price_unit,
                currency=phantom_line.currency_id,
                quantity=quantity,
                product=phantom_line.product_id,
                partner=sale_line.order_id.partner_shipping_id,
            )
            if sale_line.company_id.tax_calculation_rounding_method == (
                "round_globally"
            ):
                price_tax = sum(t.get("amount", 0.0) for t in taxes.get("taxes", []))
            else:
                price_tax = taxes["total_included"] - taxes["total_excluded"]
            phantom_line.update(
                {
                    "sale_tax_description": ", ".join(
                        t.name or t.description for t in phantom_line.sale_tax_id
                    ),
                    "sale_price_subtotal": taxes["total_excluded"],
                    "sale_price_tax": price_tax,
                    "sale_price_total": taxes["total_included"],
                    "phantom_line": True,
                    "phantom_delivered_qty": quantity,
                }
            )
            # Remove the other lines
            redundant_lines = move_lines[1:]
            if redundant_lines:
                redundant_lines.update(
                    {
                        "sale_tax_description": "",
                        "sale_price_subtotal": 0,
                        "sale_price_tax": 0,
                        "sale_price_total": 0,
                    }
                )
