# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        """Transfer the SO line description to the move name."""
        res = super()._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        if values.get("sale_line_id"):
            line = self.env["sale.order.line"].browse(values["sale_line_id"])
            # Avoid double printing the name in the picking
            pattern = f"{line.product_id.display_name}\n"
            description_picking = line.name
            if description_picking.startswith(pattern):
                description_picking = description_picking.replace(pattern, "")
            if (
                description_picking
                and description_picking != line.product_id.display_name
            ):
                res["description_picking"] = description_picking
            res["name"] = line.name
        return res
