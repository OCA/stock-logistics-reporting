# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


class CommonAverageSaleTest:
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
        # (...)
        # # [Zone Location]
        # # # [Area Location]
        # # # # [Bin Location]
        cls.location_zone = cls.location_obj.create(
            {
                "name": "Zone Location",
                "location_id": cls.warehouse_0.lot_stock_id.id,
            }
        )
        cls.location_area = cls.location_obj.create(
            {"name": "Area Location", "location_id": cls.location_zone.id}
        )
        cls.location_bin = cls.location_obj.create(
            {"name": "Bin Location", "location_id": cls.location_area.id}
        )
        cls.location_bin_2 = cls.location_obj.create(
            {"name": "Bin Location 2", "location_id": cls.location_area.id}
        )
        cls.scrap_location = cls.location_obj.create(
            {
                "name": "Scrap Location",
                "usage": "inventory",
            }
        )
        cls.stock_location = cls.env.ref("stock.warehouse0").lot_stock_id

        cls._create_products()

    @classmethod
    def _create_inventory(cls):
        cls.inventory_obj.create(
            {
                "product_id": cls.product_1.id,
                "inventory_quantity": 50.0,
                "location_id": cls.location_bin.id,
            }
        )._apply_inventory()
        cls.inventory_obj.create(
            {
                "product_id": cls.product_2.id,
                "inventory_quantity": 60.0,
                "location_id": cls.location_bin_2.id,
            }
        )._apply_inventory()

    @classmethod
    def _create_products(cls):
        cls.product_1 = cls.env["product.product"].create(
            {
                "name": "Product 1",
                "type": "product",
            }
        )
        cls.product_2 = cls.env["product.product"].create(
            {
                "name": "Product 2",
                "type": "product",
            }
        )

    @classmethod
    def _create_move(cls, product, origin_location, qty):
        move = cls.move_obj.create(
            {
                "product_id": product.id,
                "name": product.name,
                "location_id": origin_location.id,
                "location_dest_id": cls.customers.id,
                "product_uom_qty": qty,
                "priority": "1",
            }
        )
        # TODO: Check why this is necessary - it's in materialzed view query
        move.priority = "1"
        return move

    @classmethod
    def _refresh(cls):
        # Flush to allow materialized view to be correctly populated
        cls.env.flush_all()
        cls.env["stock.average.daily.sale"].refresh_view()
