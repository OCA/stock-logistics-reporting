# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    date_delay = fields.Float(
        compute="_compute_date_delay",
        store=True,
        help="If the move is done, the difference between "
        "the scheduled date and the deadline",
    )
    delivery_time = fields.Float(
        compute="_compute_delivery_time",
        store=True,
        help="If the move is done, the difference between "
        "the original scheduled date and the end date",
    )

    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_supplier",
        store=True,
        help="Partner responsible of completing the move on time.",
    )

    @api.depends("state")
    def _compute_date_delay(self):
        for rec in self:
            picking = rec.picking_id
            if rec.state == "done":
                if rec.original_date:
                    rec.date_delay = (rec.date - rec.original_date).days
                elif picking.scheduled_date:
                    rec.date_delay = (rec.date - picking.scheduled_date).days
                else:
                    rec.date_delay = 0
            else:
                rec.date_delay = None

    @api.depends("state")
    def _compute_delivery_time(self):
        for rec in self:
            if rec.state == "done":
                rec.delivery_time = (rec.date - rec.create_date).days
            else:
                rec.delivery_time = None

    @api.depends("state")
    def _compute_supplier(self):
        for rec in self:
            if rec.picking_id.picking_type_id.code == "incoming":
                rec.supplier_id = rec.picking_id.partner_id
            elif rec.picking_id.picking_type_id.code == "outgoing":
                rec.supplier_id = rec.picking_id.company_id.partner_id
