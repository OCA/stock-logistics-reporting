# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    average_daily_sale_root_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Average Daily Sale Root Location",
        compute="_compute_average_daily_sale_root_location_id",
        store=True,
        readonly=False,
        check_company=True,
        help="This is the root location for daily sale average stock computations",
    )

    @api.depends("lot_stock_id")
    def _compute_average_daily_sale_root_location_id(self):
        """
        Set a default root location from warehouse lot stock
        """
        for warehouse in self.filtered(
            lambda w: not w.average_daily_sale_root_location_id
        ):
            if not warehouse.lot_stock_id:
                continue
            warehouse.average_daily_sale_root_location_id = warehouse.lot_stock_id

    @api.model
    def create(self, vals):
        # set the lot_stock_id of a newly created WH as an Average Daily Sale Root Location
        warehouses = super().create(vals)
        for warehouse in warehouses:
            if vals.get("lot_stock_id") and not vals.get(
                "average_daily_sale_root_location_id"
            ):
                warehouse.average_daily_sale_root_location_id = vals["lot_stock_id"]
        return warehouses
