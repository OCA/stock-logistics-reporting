# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockStorageCategory(models.Model):

    _inherit = "stock.storage.category"

    void_location_ids = fields.Many2many(
        comodel_name="stock.location",
        compute="_compute_void_location_ids",
        help="These are the void locations having this storage category",
    )
    occupied_location_ids = fields.Many2many(
        comodel_name="stock.location",
        compute="_compute_void_location_ids",
        help="These are the void locations having this storage category",
    )
    void_location_count = fields.Integer(
        compute="_compute_void_location_ids",
        search="_search_void_location_count",
        help="This is the number of void locations having this storage category",
    )
    occupied_location_count = fields.Integer(
        compute="_compute_void_location_ids",
        help="This is the number of occupied locations having this storage category",
    )
    occupation_rate = fields.Float(
        compute="_compute_void_location_ids",
    )

    @api.depends("location_ids.children_ids")
    def _compute_void_location_ids(self):
        for category in self:
            all_locations = (
                category.location_ids | category.location_ids.children_ids
            ).filtered(lambda location: location.usage != "view")
            void_locations = all_locations.filtered(
                lambda location: not location.occupied
            )
            occupied_locations = all_locations - void_locations
            if all_locations:
                occupation_rate = float(
                    100 - ((len(void_locations) / len(all_locations)) * 100)
                )
            else:
                occupation_rate = 0.0
            category.update(
                {
                    "void_location_ids": void_locations.ids,
                    "occupied_location_ids": occupied_locations.ids,
                    "occupied_location_count": len(occupied_locations),
                    "void_location_count": len(void_locations),
                    "occupation_rate": occupation_rate,
                }
            )
