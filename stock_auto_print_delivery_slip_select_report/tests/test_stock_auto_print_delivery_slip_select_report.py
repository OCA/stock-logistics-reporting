# Copyright 2026 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.base.tests.common import BaseCommon


class TestStockAutoPrintDeliverySlipSelectReport(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.default_report = cls.env.ref("stock.action_report_delivery")
        cls.custom_report = cls.env.ref("stock.action_report_picking")
        cls.picking_type = cls.env.ref("stock.picking_type_out")
        cls.picking_type.auto_print_delivery_slip = True
        cls.picking_type_2 = cls.picking_type.copy(
            {"name": "Delivery 2", "sequence_code": "OUT2"}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "consu"}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})

    def _create_picking(self, picking_type):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "partner_id": self.partner.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "location_id": picking_type.default_location_src_id.id,
                            "location_dest_id": self.env.ref(
                                "stock.stock_location_customers"
                            ).id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.move_ids.quantity = 1
        return picking

    def _get_report_names(self, actions):
        return [action["report_name"] for action in actions]

    def test_default_report(self):
        self.assertEqual(self.picking_type.delivery_slip_report_id, self.default_report)
        picking = self._create_picking(self.picking_type)
        self.assertEqual(
            self._get_report_names(picking._get_autoprint_report_actions()),
            [self.default_report.report_name],
        )

    def test_empty_report_fallback(self):
        self.picking_type.delivery_slip_report_id = False
        picking = self._create_picking(self.picking_type)
        self.assertEqual(
            self._get_report_names(picking._get_autoprint_report_actions()),
            [self.default_report.report_name],
        )

    def test_custom_report(self):
        self.picking_type.delivery_slip_report_id = self.custom_report
        picking = self._create_picking(self.picking_type)
        actions = picking._get_autoprint_report_actions()
        self.assertEqual(
            self._get_report_names(actions), [self.custom_report.report_name]
        )
        self.assertEqual(actions[0]["context"]["active_ids"], picking.ids)

    def test_button_validate(self):
        self.picking_type.delivery_slip_report_id = self.custom_report
        picking = self._create_picking(self.picking_type)
        res = picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(res["tag"], "do_multi_print")
        self.assertEqual(
            self._get_report_names(res["params"]["reports"]),
            [self.custom_report.report_name],
        )
