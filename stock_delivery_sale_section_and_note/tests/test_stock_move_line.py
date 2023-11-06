# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import TestStockDeliverySaleSectionNoteCommon


class TestStockMove(TestStockDeliverySaleSectionNoteCommon):
    def test_01_prepare_section_or_note_values(self):
        with not self.assertRaises(NotImplementedError):
            move = self.env["stock.move"].search(
                [("id", "=", self.sol_product_order.id)]
            )
            move_line = self.env["stock.move.line"].search([("move_id", "=", move.id)])
            section_line = self.sale_order_line_section
            result = section_line.prepare_section_or_note_values()
            oracle = {
                "sequence": section_line.sequence,
                "display_type": section_line.display_type,
                "display_class": section_line.get_section_or_note_class(),
                "name": section_line.name,
                "description": section_line.name,
                "qty_done": 0,
                "qty_ordered": 0,
                "product_uom_id": move_line.product_uom.id,
                "product_id": move_line.product_id.id,
            }
            self.assertTrue(result, oracle)

    def test_02_inject_sections_and_notes(self):
        result = self.pickings.move_line_ids.inject_sections_and_notes()
        oracle = 7
        self.assertEqual(len(result), oracle)
