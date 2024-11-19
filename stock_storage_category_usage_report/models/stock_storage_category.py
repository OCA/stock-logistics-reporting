# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockStorageCategory(models.Model):

    _inherit = "stock.storage.category"

    empty_location_ids = fields.Many2many(
        comodel_name="stock.location",
        compute="_compute_empty_location_ids",
        help="These are the empty locations having this storage category",
    )
    filled_location_ids = fields.Many2many(
        comodel_name="stock.location",
        compute="_compute_empty_location_ids",
        help="These are the filled locations having this storage category",
    )
    empty_location_count = fields.Integer(
        compute="_compute_empty_location_ids",
        search="_search_empty_location_count",
        help="This is the number of empty locations having this storage category",
    )
    filled_location_count = fields.Integer(
        compute="_compute_empty_location_ids",
        help="This is the number of occupied locations having this storage category",
    )
    fill_rate = fields.Float(
        compute="_compute_empty_location_ids",
    )

    @api.depends("location_ids.children_ids")
    def _compute_empty_location_ids(self):
        for category in self:
            all_locations = (
                category.location_ids | category.location_ids.children_ids
            ).filtered(lambda location: location.usage != "view")
            # Empty locations are locations empty and being emptied
            # (move qty is done but not yet validated).
            # We don't take into account filled and being filled moves.
            empty_locations = all_locations.filtered(
                lambda location: location.fill_state == "empty"
            )
            filled_locations = all_locations - empty_locations
            if all_locations:
                fill_rate = float(
                    100 - ((len(empty_locations) / len(all_locations)) * 100)
                )
            else:
                fill_rate = 0.0
            category.update(
                {
                    "empty_location_ids": empty_locations.ids,
                    "filled_location_ids": filled_locations.ids,
                    "filled_location_count": len(filled_locations),
                    "empty_location_count": len(empty_locations),
                    "fill_rate": fill_rate,
                }
            )
