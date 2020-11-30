# Copyright (C) 2015 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class PickingSummaryWizard(models.TransientModel):
    _name = 'picking.summary.wizard'
    _description = 'Picking Summary Wizard'

    # Default Section
    def _default_picking_line_qty(self):
        return len(self._context.get('active_ids', []))

    def _default_picking_line_ids(self):
        picking_obj = self.env['stock.picking']
        res = []
        picking_ids = self._context.get('active_ids', [])
        for picking in picking_obj.browse(picking_ids):
            res.append((0, 0, {
                'picking_id': picking.id,
            }))
        return res

    def _default_product_line_ids(self):
        picking_obj = self.env['stock.picking']
        res = []
        product_lines = {}
        picking_ids = self.env.context.get('active_ids', [])
        # move.product_qty is real quantity with referent uom
        for picking in picking_obj.browse(picking_ids):
            for move in picking.move_lines:
                if move.product_id.id not in product_lines.keys():
                    product_lines[move.product_id.id] = {
                        'name': move.product_id.name,
                        'categ': move.product_id.categ_id.name.capitalize(),
                        'qty': move.product_qty
                    }
                else:
                    old_qty = product_lines[move.product_id.id]['qty']
                    product_lines[move.product_id.id] = {
                        'name': move.product_id.name,
                        'categ': move.product_id.categ_id.name.capitalize(),
                        'qty': old_qty + move.product_qty
                    }
        # Arranged in alphabetical order for category then product name
        product_lines_sorted = sorted(
            product_lines.items(), key=lambda x: (x[1]['categ'], x[1]['name']))
        # product_lines_sorted = sorted(
        #     dict(product_lines_sorted).items(),
        #     key=lambda x: )
        for product_id, name_qty in product_lines_sorted:
            res.append((0, 0, {
                'product_id': product_id,
                'quantity_total': name_qty['qty'],
            }))
        return res

    # Columns Section
    print_summary = fields.Boolean(
        string='Print Summary', default=True)

    print_detail = fields.Boolean(
        string='Print Detail', default=True)

    print_unity_in_list = fields.Boolean(
        string='Print Unit in Pickings List', default=True)

    product_line_ids = fields.One2many(
        comodel_name='picking.summary.wizard.product',
        inverse_name='wizard_id', default=_default_product_line_ids)

    standard_price_total = fields.Float(
        compute='_compute_standard_price_total',
        digits=dp.get_precision('Product Unit of Measure'))

    picking_line_ids = fields.One2many(
        comodel_name='picking.summary.wizard.picking',
        inverse_name='wizard_id', default=_default_picking_line_ids)

    picking_line_qty = fields.Integer(
        string='Number of Selected Picking', readonly=True,
        default=_default_picking_line_qty)

    # Compute Section
    @api.multi
    def _compute_standard_price_total(self):
        self.ensure_one()
        self.standard_price_total = sum(
            self.mapped('product_line_ids.standard_price_total'))
