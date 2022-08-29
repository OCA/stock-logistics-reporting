from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    cmr_code = fields.Integer(
        string="CMR Code",
        default=0,
        help="Code needed for CMR Report",
    )
