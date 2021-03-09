# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPikcingBatch(models.Model):
    _inherit = "stock.picking.batch"

    def get_out_pickings(self):
        for rec in self:
            # TO BE Modified Later
            # if (
            # rec.picking_type_id.warehouse_id
            # and rec.picking_type_id.warehouse_id.delivery_steps != "pick_ship"
            #             ):
            #                 raise UserError(
            #                         _(
            #                             "This report is only available for "
            #                    "warehouses configured with 2-steps delivery"
            #                         )
            #                     )
            out_pickings = (
                rec.mapped("move_ids").mapped("move_dest_ids").mapped("picking_id")
            )
        return out_pickings
