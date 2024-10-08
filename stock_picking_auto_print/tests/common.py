# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class StockPickingAutoPrintCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ModelDataObj = cls.env["ir.model.data"]
        cls.picking_type_in = cls.env["stock.picking.type"].browse(
            cls.ModelDataObj._xmlid_to_res_id("stock.picking_type_in")
        )
        cls.picking_type_out = cls.env["stock.picking.type"].browse(
            cls.ModelDataObj._xmlid_to_res_id("stock.picking_type_out")
        )
        cls.customer_location = cls.env["stock.location"].browse(
            cls.ModelDataObj._xmlid_to_res_id("stock.stock_location_customers")
        )
        cls.supplier_location = cls.env["stock.location"].browse(
            cls.ModelDataObj._xmlid_to_res_id("stock.stock_location_suppliers")
        )
        cls.stock_location = cls.env["stock.location"].browse(
            cls.ModelDataObj._xmlid_to_res_id("stock.stock_location_stock")
        )

        # Active auto print after validate
        (cls.picking_type_out + cls.picking_type_in).auto_print_delivery_slip = True

        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Test por auto print",
                "type": "product",
                "categ_id": cls.env.ref("product.product_category_all").id,
            }
        )

    def _create_picking(self, picking_type, products):
        if picking_type == self.picking_type_out:
            location = self.stock_location
            location_dest = self.customer_location
        else:
            location = self.supplier_location
            location_dest = self.stock_location

        return self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.supplier_location.id,
                            "product_uom_qty": 1,
                        },
                    )
                    for product in products
                ],
            }
        )
