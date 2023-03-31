# Copyright 2023 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo.tests import tagged

from odoo.addons.product_sticker.tests.common import ProductStickerCommon

from ..models.stock_picking_type import REPORT_STICKER_POSITIONS


@tagged("post_install", "-at_install")
class ProductStickerStockCommon(ProductStickerCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.picking_type_out.show_product_stickers = REPORT_STICKER_POSITIONS[0][0]
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.supplier_location = cls.env.ref("stock.stock_location_suppliers")

    def _create_picking(self, picking_type, products):
        return self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.supplier_location.id,
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
