# Copyright 2024 Moduon Team S.L.
# License GPL-3.0 (https://www.gnu.org/licenses/gpl-3.0)


from odoo import fields, models


class ModelName(models.Model):
    _inherit = "stock.picking.type"

    summary_qty_undelivered = fields.Boolean(
        "Print a summary with undelivered qty",
        help="Print a summary with undelivered quantity in the picking report",
    )
