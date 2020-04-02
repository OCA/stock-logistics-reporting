# Copyright 2020 Open Source Intgerators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta
from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    def _compute_quantities_in_dict(self, from_date):
        # Filter locations from context -> (quant, in, out)
        domain_locs = self._get_domain_locations()
        domain_base = [
            ('product_id', 'in', self.ids),
            ('date', '>=', from_date)]
        domain_in = domain_locs[1] + domain_base + [
            ('picking_id.picking_type_id.code',
             'in', ['incoming', 'mrp_operation'])]
        domain_return = domain_locs[2] + domain_base + [
            ('location_dest_id.usage',
             'in', ['supplier', 'inventory'])  # loss
            ]
        Move = self.env['stock.move']
        moves_in = {
            item['product_id'][0]: item['product_qty']
            for item in Move.read_group(
                domain_in,
                ['product_id', 'product_qty'],
                ['product_id'])}
        moves_return = {
            item['product_id'][0]: item['product_qty']
            for item in Move.read_group(
                domain_return,
                ['product_id', 'product_qty'],
                ['product_id'])}
        return {
            x.id: (
                moves_in.get(x.id, 0)
                - moves_return.get(x.id, 0))
            for x in self}

    def _compute_inventory_turn_report(self):
        month = relativedelta(month=1)
        today = fields.Date.today()
        at_6m_ago = today - 6 * month
        at_12m_ago = today - 12 * month
        available6m = {
            x.id: x.qty_available
            for x in self.with_context(to_date=at_6m_ago)}
        available12m = {
            x.id: x.qty_available
            for x in self.with_context(to_date=at_12m_ago)}
        gotten6m = self._compute_quantities_in_dict(from_date=at_6m_ago)
        gotten12m = self._compute_quantities_in_dict(from_date=at_12m_ago)
        for prod in self:
            prod.total_cost = prod.qty_available * prod.standard_price
            # Quantity initially available
            prod.qty_available_6m = available6m.get(prod.id)
            prod.qty_available_12m = available12m.get(prod.id)
            # Quantity gotten (produced + procured)
            prod.qty_gotten_6m = gotten6m.get(prod.id)
            prod.qty_gotten_12m = gotten12m.get(prod.id)
            # Quantity consumed in period
            prod.qty_consumed_6m = (
                prod.qty_available_6m
                + prod.qty_gotten_6m
                - prod.qty_available)
            prod.qty_consumed_12m = (
                prod.qty_available_12m
                + prod.qty_gotten_12m
                - prod.qty_available)
            # Months of Inventory
            prod.months_of_inventory_6m = (
                0.0 if not prod.qty_consumed_6m else
                prod.qty_available / prod.qty_consumed_6m * 6)
            prod.months_of_inventory_12m = (
                0.0 if not prod.qty_consumed_12m else
                prod.qty_available / prod.qty_consumed_12m * 12)
            # Turns / Cycles per Month
            prod.inventory_turns_6m = (
                0.0 if not prod.months_of_inventory_6m else
                12 / prod.months_of_inventory_6m)
            prod.inventory_turns_12m = (
                0.0 if not prod.months_of_inventory_12m else
                12 / prod.months_of_inventory_12m)

    total_cost = fields.Float(
        compute="_compute_inventory_turn_report",
        help="= Qty. on hand x Current Cost")
    qty_available_6m = fields.Float(
        name="Qty. 6m Ago",
        compute="_compute_inventory_turn_report",
        help="Qty. on hand 6 months ago")
    qty_gotten_6m = fields.Float(
        name="Qty. Gotten 6m",
        compute="_compute_inventory_turn_report",
        help="Qty. Procured or Produced in the the last 6 months")
    qty_consumed_6m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Qty. consumed in the the last 6 months")
    months_of_inventory_6m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Months of Inventory, in the last 6 months")
    inventory_turns_6m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Inventory Turns / Cycles in the last 6 months")
    qty_available_12m = fields.Float(
        name="Qty. 12m ago",
        compute="_compute_inventory_turn_report",
        help="= Qty. on hand 12 months ago")
    qty_gotten_12m = fields.Float(
        name="Qty. Gotten 12m",
        compute="_compute_inventory_turn_report",
        help="Qty. Procured or Produced in the the last 12 months")
    qty_consumed_12m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Qty. consumed in the the last 12 months")
    months_of_inventory_12m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Months of Inventory, in the last 12 months")
    inventory_turns_12m = fields.Float(
        compute="_compute_inventory_turn_report",
        help="Inventory Turns / Cycles in the last 12 months")
