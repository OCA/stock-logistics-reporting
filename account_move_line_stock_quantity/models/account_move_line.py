# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    stock_quantity = fields.Float(
        digits="Product Unit of Measure",
        help="Quantity, in the product's base unit of measure, moved by the stock "
        "operation that generated this journal item: positive for incoming "
        "valuation entries, negative for outgoing ones. Left at 0 on manually "
        "created entries and on pure monetary adjustments, such as landed costs "
        "or price differences, that do not correspond to a physical stock move.",
    )
