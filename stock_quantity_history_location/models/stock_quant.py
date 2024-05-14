# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options=options)
        user_has_group = self.user_has_groups("stock.group_stock_multi_locations")
        list_view = res.get("views", {}).get("list", {})
        if user_has_group and list_view:
            arch = list_view.get("arch", "")
            arch_tree = etree.XML(arch)
            buttons = arch_tree.xpath('//button[@name="action_inventory_at_date"]')
            for button in buttons:
                button.set("string", "Inventory at Date & Location")
            new_arch = etree.tostring(arch_tree, encoding="unicode")
            list_view["arch"] = new_arch
        return res
