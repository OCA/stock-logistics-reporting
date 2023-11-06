# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import TestStockDeliverySaleSectionNoteCommon


class TestStockMove(TestStockDeliverySaleSectionNoteCommon):
    def test_01_prepare_section_or_note_values(self):
        with not self.assertRaises(NotImplementedError):
            move = self.env["stock.move"].search(
                [("id", "=", self.sol_product_order.id)]
            )
            section_line = self.sale_order_line_section
            result = section_line.prepare_section_or_note_values()
            oracle = {
                "sequence": section_line.sequence,
                "display_type": section_line.display_type,
                "name": section_line.name,
                "date": result["date"],
                "company_id": section_line.company_id.id,
                "product_id": move.product_id.id,
                "product_uom_qty": 0,
                "product_uom": move.product_uom.id,
                "location_id": False,
                "location_dest_id": False,
                "procure_method": False,
            }
            self.assertTrue(result, oracle)

    def test_02_inject_sections_and_notes(self):
        result = self.pickings.move_lines.inject_sections_and_notes()
        oracle = 7
        self.assertEqual(len(result), oracle)
