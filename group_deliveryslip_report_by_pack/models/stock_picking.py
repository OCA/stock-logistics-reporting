# -*- coding: utf-8 -*-
# © 2017 Nicola Malcontenti - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

from odoo import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def grouped_lines_by_pack(self, picking_id):
        line_grouped_for_pack = {}
        for line in self.pack_operation_product_ids:
            group_key = line.result_package_id.name
            if group_key in line_grouped_for_pack:
                line_grouped_for_pack[group_key].append(line)
            else:
                line_grouped_for_pack[group_key] = [line]
        return_lists = []
        for pack_name in line_grouped_for_pack:
            return_lists.append(line_grouped_for_pack[pack_name])
        return return_lists
