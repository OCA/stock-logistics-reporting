# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo.fields import Datetime
from odoo.tests.common import TransactionCase


class CommonAverageSaleTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.inventory_obj = cls.env["stock.quant"].with_context(inventory_mode=True)
        cls.customers = cls.env.ref("stock.stock_location_customers")
        cls.location_obj = cls.env["stock.location"]
        cls.move_obj = cls.env["stock.move"]
        cls.warehouse_0 = cls.env.ref("stock.warehouse0")
        cls.average_sale_obj = cls.env["stock.average.daily.sale"]
        cls.average_sale_obj._create_materialized_view()
        cls.view_cron = cls.env.ref(
            "stock_average_daily_sale.refresh_materialized_view"
        )
        # Create the following structure:
        # [Stock]
        # # [Zone Location]
        # # # [Bin Location]
        cls.location_zone = cls.location_obj.create(
            {
                "name": "Zone Location",
                "location_id": cls.warehouse_0.lot_stock_id.id,
            }
        )
        cls.location_bin = cls.location_obj.create(
            {"name": "Bin Location", "location_id": cls.location_zone.id}
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Product 1",
                "type": "product",
            }
        )

        cls.cfg = cls.env["stock.average.daily.sale.config"].search(
            [
                ("warehouse_id", "=", cls.warehouse_0.id),
                ("location_id", "=", cls.warehouse_0.lot_stock_id.id),
                ("abc_classification_level", "=", cls.product.abc_storage),
            ]
        )
        cls.cfg.update(
            {
                "period_value": 1,
                "period_name": "week",
                "exclude_weekends": False,
            }
        )
        cls.cfg.location_id = cls.location_zone

        cls.now = Datetime.now()
        cls.inventory_date = Datetime.to_string(
            cls.now - relativedelta(cls.now, weeks=30)
        )
        with freeze_time(cls.inventory_date):
            cls.inventory_obj.create(
                {
                    "product_id": cls.product.id,
                    "inventory_quantity": 50.0,
                    "location_id": cls.location_bin.id,
                }
            )._apply_inventory()

    @classmethod
    def _create_move(cls, product, origin_location, qty):
        move = cls.move_obj.create(
            {
                "product_id": product.id,
                "name": product.name,
                "location_id": origin_location.id,
                "location_dest_id": cls.customers.id,
                "product_uom_qty": qty,
            }
        )
        return move

    @classmethod
    def _make_move(cls, product, origin_location, qty):
        move = cls._create_move(product, origin_location, qty)
        move._action_confirm()
        move._action_assign()
        move.quantity_done = move.product_uom_qty
        move._action_done()

    @classmethod
    def _refresh(cls):
        # Flush to allow materialized view to be correctly populated
        cls.env.flush_all()
        cls.env["stock.average.daily.sale"].refresh_view()
