# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from lxml import html as lxml_html

from odoo import Command
from odoo.tests.common import HttpCase


class TestStockPickingReportWithoutOrderQty(HttpCase):
    ordered_qty = 17
    delivered_qty = 11
    backorder_qty = 6

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.write(
            {
                "group_ids": [
                    Command.link(cls.env.ref("stock.group_lot_on_delivery_slip").id)
                ]
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls._create_product("WOQ Untracked Product")

    @classmethod
    def _create_product(cls, name, tracking="none"):
        return cls.env["product.product"].create(
            {
                "name": name,
                "type": "consu",
                "is_storable": True,
                "tracking": tracking,
            }
        )

    def _create_picking(self, product=None, lot=None):
        product = product or self.product
        self.env["stock.quant"]._update_available_quantity(
            product,
            self.warehouse.lot_stock_id,
            self.ordered_qty,
            lot_id=lot,
        )
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        self.env["stock.move"].create(
            {
                "product_id": product.id,
                "product_uom_qty": self.ordered_qty,
                "product_uom": product.uom_id.id,
                "picking_id": picking.id,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_line_ids.write(
            {
                "quantity": self.delivered_qty,
                **({"lot_id": lot.id} if lot else {}),
            }
        )
        return picking

    def _complete_picking(self, picking, create_backorder=False):
        picking.move_ids.picked = True
        picking.with_context(cancel_backorder=not create_backorder)._action_done()
        self.assertEqual(picking.state, "done")
        return picking

    def _render_report(self, picking):
        report = self.env["ir.actions.report"]
        content, report_type = report._render_qweb_html(
            "stock.action_report_delivery", picking.ids
        )
        self.assertEqual(report_type, "html")
        return lxml_html.fromstring(content)

    def _single(self, document, expression):
        nodes = document.xpath(expression)
        self.assertEqual(len(nodes), 1, expression)
        return nodes[0]

    @staticmethod
    def _text(node):
        return " ".join(node.text_content().split())

    @staticmethod
    def _column_count(row):
        return sum(int(cell.get("colspan", "1")) for cell in row.xpath("./th | ./td"))

    def test_not_done_report_shows_ordered_quantities(self):
        picking = self._create_picking()

        document = self._render_report(picking)
        table = self._single(document, "//table[@name='stock_move_table']")

        self.assertEqual(len(table.xpath(".//th[@name='th_sm_ordered']")), 1)
        self.assertEqual(len(table.xpath(".//th[@name='th_sm_quantity']")), 1)
        table_text = self._text(table)
        self.assertIn(str(self.ordered_qty), table_text)
        self.assertIn(str(self.delivered_qty), table_text)

    def test_done_aggregated_report_hides_ordered_quantities(self):
        picking = self._complete_picking(self._create_picking())

        document = self._render_report(picking)
        table = self._single(document, "//table[@name='stock_move_line_table']")

        self.assertFalse(table.xpath(".//th[@name='th_sml_qty_ordered']"))
        self.assertFalse(table.xpath(".//th[@name='lot_serial']"))
        self.assertFalse(table.xpath(".//td[@name='move_line_aggregated_qty_ordered']"))
        self.assertTrue(table.xpath(".//td[@name='move_line_aggregated_quantity']"))
        table_text = self._text(table)
        self.assertIn(str(self.delivered_qty), table_text)
        self.assertNotIn(str(self.ordered_qty), table_text)

    def test_done_lot_report_shows_lot_only_when_present(self):
        tracked_product = self._create_product("WOQ Lot Product", tracking="lot")
        lot = self.env["stock.lot"].create(
            {"name": "WOQ-LOT-UNIQUE", "product_id": tracked_product.id}
        )
        tracked_picking = self._complete_picking(
            self._create_picking(product=tracked_product, lot=lot)
        )

        tracked_document = self._render_report(tracked_picking)
        tracked_table = self._single(
            tracked_document, "//table[@name='stock_move_line_table']"
        )
        self.assertFalse(tracked_table.xpath(".//th[@name='th_sml_qty_ordered']"))
        self.assertEqual(len(tracked_table.xpath(".//th[@name='lot_serial']")), 1)
        self.assertIn(lot.name, self._text(tracked_table))
        self.assertIn(str(self.delivered_qty), self._text(tracked_table))

        untracked_picking = self._complete_picking(self._create_picking())
        untracked_document = self._render_report(untracked_picking)
        untracked_table = self._single(
            untracked_document, "//table[@name='stock_move_line_table']"
        )
        self.assertFalse(untracked_table.xpath(".//th[@name='lot_serial']"))

    def test_done_package_report_keeps_columns_aligned(self):
        picking = self._create_picking()
        package = picking.action_put_in_pack(package_name="WOQ-PACKAGE-UNIQUE")
        self._complete_picking(picking)

        document = self._render_report(picking)
        table = self._single(document, "//table[@name='stock_move_line_table']")
        header = self._single(table, ".//thead/tr")
        rows = table.xpath(".//tbody/tr[not(contains(@class, 'o_line_section'))]")

        self.assertIn(package.name, self._text(table))
        self.assertFalse(table.xpath(".//td[@name='move_line_aggregated_qty_ordered']"))
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(self._column_count(row), self._column_count(header))

    def test_partial_delivery_keeps_backorder_quantities(self):
        picking = self._complete_picking(self._create_picking(), create_backorder=True)

        self.assertTrue(picking.backorder_ids)
        document = self._render_report(picking)
        completed_table = self._single(
            document, "//table[@name='stock_move_line_table']"
        )
        backorder_table = self._single(
            document, "//table[@name='stock_backorder_table']"
        )

        self.assertFalse(
            completed_table.xpath(".//td[@name='move_line_aggregated_qty_ordered']")
        )
        self.assertIn(str(self.backorder_qty), self._text(backorder_table))

    def test_done_delivery_slip_pdf_renders(self):
        picking = self._complete_picking(self._create_picking())

        content, report_type = (
            self.env["ir.actions.report"]
            .with_context(force_report_rendering=True)
            ._render("stock.action_report_delivery", picking.ids)
        )

        self.assertEqual(report_type, "pdf")
        self.assertTrue(content.startswith(b"%PDF"))
