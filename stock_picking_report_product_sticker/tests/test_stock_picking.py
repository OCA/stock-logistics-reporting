# Copyright 2023 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from .common import ProductStickerStockCommon


class TestStickersOnPickings(ProductStickerStockCommon):
    def test_stock_picking(self):
        target_product = self.product_as400.product_variant_ids[0]
        product_stickers = target_product.get_product_stickers()
        picking = self._create_picking(
            self.picking_type_out, [target_product, target_product]
        )
        self.assertEqual(
            picking.show_product_stickers,
            self.picking_type_out.show_product_stickers,
            "Picking type should show stickers",
        )
        self.assertEqual(
            picking.sticker_ids,
            product_stickers,
            "Not the same images than the product",
        )
