# Copyright 2021 ACSONE SA/NV
# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

from odoo.addons.stock_storage_type_putaway_abc.models.stock_location import (
    ABC_SELECTION,
)


class StockAverageDailySaleConfig(models.Model):
    _name = "stock.average.daily.sale.config"
    _description = "Average daily sales computation parameters"
    check_company_auto = True

    active = fields.Boolean(default=True)
    abc_classification_level = fields.Selection(
        selection=ABC_SELECTION, required=True, default="b"
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    warehouse_id = fields.Many2one(
        string="Warehouse",
        comodel_name="stock.warehouse",
        required=True,
        ondelete="cascade",
        check_company=True,
        default=lambda self: self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        ),
    )
    location_id = fields.Many2one(
        string="Location",
        comodel_name="stock.location",
        compute="_compute_average_daily_sale_root_location_id",
        store=True,
        required=True,
        readonly=False,
        precompute=True,
        check_company=True,
    )
    exclude_weekends = fields.Boolean(
        help="Set to True only if you do not expect any orders/deliveries during "
        "the weekends. If set to True, stock moves done on weekends won't be "
        "taken into account to calculate the average daily usage",
    )
    period_name = fields.Selection(
        string="Period analyzed unit",
        selection=[
            ("year", "Years"),
            ("month", "Months"),
            ("week", "Weeks"),
            ("day", "Days"),
        ],
        required=True,
    )
    period_value = fields.Integer("Period analyzed value", required=True)
    number_days_qty_in_stock = fields.Integer(
        string="Number of days of quantities in stock", required=True, default=2
    )
    safety_factor = fields.Float(digits=(2, 2), required=True)

    _sql_constraints = [
        (
            "abc_classification_level_unique",
            "UNIQUE(abc_classification_level, location_id)",
            _("Abc Classification Level must be unique per location"),
        )
    ]

    @api.depends("warehouse_id")
    def _compute_average_daily_sale_root_location_id(self):
        """
        Set a default root location from warehouse lot stock
        """
        for rec in self:
            if not rec.warehouse_id.lot_stock_id:
                rec.location_id = False
            else:
                rec.location_id = rec.warehouse_id.lot_stock_id
