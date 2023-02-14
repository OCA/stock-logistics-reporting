# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AbcClassificationProfile(models.Model):

    _inherit = "abc.classification.profile"

    stock_average_daily_sale_config_ids = fields.One2many(
        comodel_name="stock.average.daily.sale.config",
        inverse_name="abc_classification_profile_id",
        string="Average Daily Sale Configurations",
    )
