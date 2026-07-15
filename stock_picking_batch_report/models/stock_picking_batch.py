# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPikcingBatch(models.Model):
    _inherit = "stock.picking.batch"

    def get_out_pickings(self):
        return self.mapped("move_ids.move_dest_ids.picking_id")
