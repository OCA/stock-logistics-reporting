# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase


class TestStockMoveDelayReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({"name": "Delay Supplier"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Delay Product",
                "is_storable": True,
            }
        )
        cls.in_type = cls.env.ref("stock.picking_type_in")
        cls.out_type = cls.env.ref("stock.picking_type_out")

    def _create_picking(self, picking_type, partner=False):
        return self.env["stock.picking"].create(
            {
                "partner_id": partner and partner.id,
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": picking_type.default_location_dest_id.id,
                "scheduled_date": fields.Datetime.now(),
            }
        )

    def _create_done_move(self, picking_type, partner=False, delay_days=0):
        picking = self._create_picking(picking_type, partner=partner)
        move = self.env["stock.move"].create(
            {
                "picking_id": picking.id,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 1.0,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
            }
        )
        original_date = move.create_date + timedelta(days=1)
        move.write(
            {
                "date": original_date + timedelta(days=delay_days),
                "original_date": original_date,
                "state": "done",
            }
        )
        self.env.flush_all()
        return move

    def test_incoming_move_delay_report_values(self):
        move = self._create_done_move(self.in_type, partner=self.partner, delay_days=2)

        self.assertEqual(move.supplier_id, self.partner)
        self.assertEqual(move.date_delay, 2)
        self.assertEqual(move.delivery_time, 3)

        report = self.env["stock.move.delay.report"].search([("move_id", "=", move.id)])
        self.assertEqual(len(report), 1)
        self.assertEqual(report.supplier_id, self.partner)
        self.assertEqual(report.date_delay, 2)
        self.assertEqual(report.done_on_time, 0.0)

    def test_outgoing_move_delay_report_values(self):
        move = self._create_done_move(self.out_type, delay_days=0)

        self.assertEqual(move.supplier_id, self.company.partner_id)
        self.assertEqual(move.date_delay, 0)

        report = self.env["stock.move.delay.report"].search([("move_id", "=", move.id)])
        self.assertEqual(len(report), 1)
        self.assertEqual(report.supplier_id, self.company.partner_id)
        self.assertEqual(report.done_on_time, 100.0)

    def test_supplier_is_cleared_without_responsible_partner(self):
        move = self._create_done_move(self.in_type, partner=self.partner, delay_days=1)
        self.assertEqual(move.supplier_id, self.partner)

        move.picking_id = False
        self.assertFalse(move.supplier_id)

    def test_multi_company_rule_limits_report_rows(self):
        other_company = self.env["res.company"].create({"name": "Other Delay Company"})
        other_partner = self.env["res.partner"].create({"name": "Other Supplier"})
        self._create_done_move(self.in_type, partner=self.partner, delay_days=1)
        other_move = self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 1.0,
                "location_id": self.in_type.default_location_src_id.id,
                "location_dest_id": self.in_type.default_location_dest_id.id,
                "company_id": other_company.id,
                "date": fields.Datetime.now(),
                "state": "done",
            }
        )
        self.env.cr.execute(
            """
            UPDATE stock_move
               SET supplier_id = %s
             WHERE id = %s
            """,
            [other_partner.id, other_move.id],
        )
        self.env.flush_all()

        user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Delay Report User",
                    "login": "delay_report_user",
                    "email": "delay_report_user@example.com",
                    "company_id": self.company.id,
                    "company_ids": [(6, 0, [self.company.id])],
                    "all_group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
                }
            )
        )
        reports = self.env["stock.move.delay.report"].with_user(user).search([])

        self.assertNotIn(other_move.id, reports.mapped("move_id").ids)
