# Copyright 2024 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from .common import StockPickingAutoPrintCommon, tagged


@tagged("-at_install", "post_install")
class TestStockPickingAutoPrint(StockPickingAutoPrintCommon):
    def test_incoming_picking_reception_report(self):
        """Test a complex case. Automatic reception report activates, so the
        delivery slip must be downloaded and other action must be opened.
        """
        self.env.user.groups_id += self.env.ref("stock.group_reception_report")
        self.env.user.groups_id += self.env.ref("stock.group_auto_reception_report")

        picking_out = self._create_picking(self.picking_type_out, self.product1)
        picking_out.action_assign()

        picking_in = self._create_picking(self.picking_type_in, self.product1)
        picking_in.action_confirm()
        picking_in.action_assign()
        picking_in.move_lines.quantity_done = 1
        res = picking_in.button_validate()
        reports = res["actions"][0]
        annother_action = res["actions"][1]
        self.assertEqual(annother_action["xml_id"], "stock.stock_reception_action")
        self.assertEqual(reports["report_name"], "stock.report_deliveryslip")
