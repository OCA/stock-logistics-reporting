# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import _, api, models
from odoo.fields import Date, Datetime

_logger = logging.getLogger(__name__)


class StockAverageDailySaleDemo(models.TransientModel):

    _name = "stock.average.daily.sale.demo"
    _description = "Wizard to populate demo data with past moves for Average Daily Sale"

    def _create_move(self, product, origin_location, qty):
        suppliers = self.env.ref("stock.stock_location_suppliers")
        customers = self.env.ref("stock.stock_location_customers")
        move_obj = self.env["stock.move"]
        # Create first an incoming move to avoid negative quantities
        move = move_obj.create(
            {
                "product_id": product.id,
                "name": product.name,
                "location_id": suppliers.id,
                "location_dest_id": customers.id,
                "product_uom_qty": qty,
            }
        )
        move._action_confirm()
        move._action_assign()
        move.quantity_done = move.product_uom_qty
        move._action_done()

        # Create the OUT move
        move = move_obj.create(
            {
                "product_id": product.id,
                "name": product.name,
                "location_id": origin_location.id,
                "location_dest_id": customers.id,
                "product_uom_qty": qty,
                "priority": "1",
            }
        )
        return move

    @api.model
    def _create_movement(self, product):
        now = Datetime.now()
        stock = self.env.ref("stock.stock_location_stock")
        move_1_date = Date.to_string(now - relativedelta(weeks=11))
        with freeze_time(move_1_date):
            move = self._create_move(product, stock, 10.0)
            move._action_confirm()
            move._action_assign()
            move.quantity_done = move.product_uom_qty
            move._action_done()
            move.priority = "1"
        move_2_date = Date.to_string(now - relativedelta(weeks=9))
        with freeze_time(move_2_date):
            move = self._create_move(product, stock, 12.0)
            move._action_confirm()
            move._action_assign()
            move.quantity_done = move.product_uom_qty
            move._action_done()
            move.priority = "1"

    @api.model
    def _action_create_data(self):
        """
        This is called through an xml function in order to populate
        demo data with past moves as the report depends on that.
        """
        module = self.env["ir.module.module"].search(
            [("name", "=", "stock_average_daily_sale"), ("demo", "=", True)]
        )
        if not module:
            _logger.warning(
                _("You cannot call the _action_create_data() on production database.")
            )
            return
        product = self.env["product.product"].create(
            {
                "name": "Product Test 1",
                "type": "product",
            }
        )
        self._create_movement(product)
        product = self.env["product.product"].create(
            {
                "name": "Product Test 2",
                "type": "product",
            }
        )
        self._create_movement(product)

        self.env["stock.average.daily.sale"].refresh_view()
