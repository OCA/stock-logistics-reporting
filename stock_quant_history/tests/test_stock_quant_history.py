# Copyright 2025 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import users

from . import common


class TestStockQuantHistory(common.TestStockQuantHistoryCommon):
    def test_compare_quant(self):
        self.stock_history_now.action_generate_stock_quant_history()
        self.assertQuantCompare(
            self.stock_history_now.stock_quant_history_ids,
            self.env["stock.quant"].search(
                [
                    (
                        "location_id.usage",
                        "not in",
                        [
                            "customer",
                            "inventory",
                            "supplier",
                        ],
                    ),
                ]
            ),
        )

    @users("stock_manager")
    def test_unlink_snapshot_unlink_related_stock_quant_history_records(self):
        # browse with current user
        self.stock_history_now.action_generate_stock_quant_history()
        stock_history_now = self.env["stock.quant.history.snapshot"].browse(
            self.stock_history_now.id
        )
        stock_quant_history_ids = stock_history_now.stock_quant_history_ids.ids
        self.assertTrue(
            len(stock_quant_history_ids) > 0,
        )
        stock_history_now.unlink()
        self.assertEqual(
            self.env["stock.quant.history"].search_count(
                [("id", "in", stock_quant_history_ids)]
            ),
            0,
        )

    @users("stock_manager")
    def test_unlink_stock_quant_history_is_forbidden(self):
        # browse with current user
        self.stock_history_now.action_generate_stock_quant_history()
        stock_history_now = self.env["stock.quant.history.snapshot"].browse(
            self.stock_history_now.id
        )
        with self.assertRaisesRegex(
            AccessError, r"You are not allowed to delete.*stock.quant.histor.*"
        ):
            stock_history_now.stock_quant_history_ids.unlink()

    @users("stock_manager")
    def test_stock_manager_create(self):
        stock_history_now = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("1984-06-15 11:22:32"),
            }
        )
        self.assertEqual(
            stock_history_now.name,
            # en_US format
            "Snapshot 06/15/1984 11:22:32",
        )
        stock_history_now.inventory_date = fields.Datetime.now()
        stock_history_now.action_generate_stock_quant_history()

    @freeze_time("2024-01-01 10:11")
    def test_no_lines_before_oldest_move(self):
        stock_history_1970 = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("1970-01-01"),
            }
        )
        stock_history_1970.action_generate_stock_quant_history()
        self.assertEqual(
            stock_history_1970.generated_date,
            fields.Datetime.from_string("2024-01-01 10:11"),
        )
        self.assertEqual(stock_history_1970.state, "generated")
        self.assertEqual(len(stock_history_1970.stock_quant_history_ids), 0)

    def test_round_decimal_using_uom_precision(self):
        with freeze_time("2023-01-01 10:00:00"):
            self._update_product_stock(10.001)

        with freeze_time("2023-01-01 20:00:00"):
            self._update_product_stock(20.002)

        snapshot_10 = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-01-01 10:00:00"),
            }
        )
        snapshot_10.action_generate_stock_quant_history()
        quant_history_10 = snapshot_10.stock_quant_history_ids.filtered(
            lambda quant_history,
            pdt=self.product,
            loc=self.location: quant_history.product_id == pdt
            and quant_history.location_id == loc
        )
        # force wrong rounding for testing purpose adding float in python can be tricky
        # >>> 0.1 + 0.1 + 0.1
        # 0.30000000000000004

        quant_history_10.quantity = 10.001
        snapshot_20 = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-01-01 20:00:00"),
            }
        )
        snapshot_20.action_generate_stock_quant_history()
        quant_history_20 = snapshot_20.stock_quant_history_ids.filtered(
            lambda quant_history,
            pdt=self.product,
            loc=self.location: quant_history.product_id == pdt
            and quant_history.location_id == loc
        )
        self.assertEqual(quant_history_20.quantity, 20)

    def test_next_quant_history_generation(self):
        with freeze_time("2023-01-01 10:00:00"):
            self._update_product_stock(10)

        with freeze_time("2023-01-01 20:00:00"):
            self._update_product_stock(30)

        snapshot_10 = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-01-01 10:00:00"),
            }
        )
        snapshot_10.action_generate_stock_quant_history()
        quant_history_10 = snapshot_10.stock_quant_history_ids.filtered(
            lambda quant_history,
            pdt=self.product,
            loc=self.location: quant_history.product_id == pdt
            and quant_history.location_id == loc
        )
        self.assertEqual(quant_history_10.quantity, 10)

        snapshot_15 = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-01-01 15:00:00"),
            }
        )
        snapshot_15.action_generate_stock_quant_history()
        quant_history_15 = snapshot_15.stock_quant_history_ids.filtered(
            lambda quant_history,
            pdt=self.product,
            loc=self.location: quant_history.product_id == pdt
            and quant_history.location_id == loc
        )
        self.assertEqual(quant_history_15.quantity, 10)
        self.assertNotEqual(quant_history_10, quant_history_15)
        self.assertNotEqual(
            quant_history_10.inventory_date, quant_history_15.inventory_date
        )
        snapshot_20 = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-01-01 20:00:00"),
            }
        )
        snapshot_20.action_generate_stock_quant_history()
        quant_history_20 = snapshot_20.stock_quant_history_ids.filtered(
            lambda quant_history,
            pdt=self.product,
            loc=self.location: quant_history.product_id == pdt
            and quant_history.location_id == loc
        )
        self.assertEqual(quant_history_20.quantity, 30)

        snapshot_now = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.now(),
            }
        )
        snapshot_now.action_generate_stock_quant_history()
        self.assertQuantCompare(
            snapshot_now.stock_quant_history_ids,
            self.env["stock.quant"].search(
                [
                    (
                        "location_id.usage",
                        "not in",
                        [
                            "customer",
                            "inventory",
                            "supplier",
                        ],
                    ),
                ]
            ),
        )

    def test_quant_0_not_present(self):
        with freeze_time("2023-01-01 10:00:00"):
            self._update_product_stock(10)

        with freeze_time("2023-01-01 15:00:00"):
            self._update_product_stock(0)

        with freeze_time("2023-01-01 20:00:00"):
            self._update_product_stock(30)

        snapshot_10 = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-01-01 10:00:00"),
            }
        )
        snapshot_10.action_generate_stock_quant_history()
        self.assertFalse(snapshot_10.previous_snapshot_id)
        quant_history_10 = snapshot_10.stock_quant_history_ids.filtered(
            lambda quant_history,
            pdt=self.product,
            loc=self.location: quant_history.product_id == pdt
            and quant_history.location_id == loc
        )
        self.assertEqual(quant_history_10.quantity, 10)

        self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-01-01 12:00:00"),
            }
        )
        snapshot_15 = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-01-01 15:00:00"),
            }
        )
        snapshot_15.action_generate_stock_quant_history()
        self.assertEqual(snapshot_15.previous_snapshot_id, snapshot_10)
        quant_history_15 = snapshot_15.stock_quant_history_ids.filtered(
            lambda quant_history,
            pdt=self.product,
            loc=self.location: quant_history.product_id == pdt
            and quant_history.location_id == loc
        )
        self.assertFalse(
            quant_history_15.exists(),
        )

        snapshot_20 = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-01-01 20:00:00"),
            }
        )
        snapshot_20.action_generate_stock_quant_history()
        self.assertEqual(snapshot_20.previous_snapshot_id, snapshot_15)
        quant_history_20 = snapshot_20.stock_quant_history_ids.filtered(
            lambda quant_history,
            pdt=self.product,
            loc=self.location: quant_history.product_id == pdt
            and quant_history.location_id == loc
        )
        self.assertEqual(quant_history_20.quantity, 30)

    def test_action_related_stock_quant_history_tree_view(self):
        self.assertEqual(
            self.stock_history_now.action_related_stock_quant_history_tree_view()[
                "domain"
            ],
            [("snapshot_id", "in", self.stock_history_now.ids)],
        )

    def test_consu_product_are_ignored(self):
        with freeze_time("2023-01-01 09:00:00"):
            # Create stock picking with consumable
            picking = self.env["stock.picking"].create(
                {
                    "location_id": self.env.ref("stock.stock_location_customers").id,
                    "location_dest_id": self.location.id,
                    "picking_type_id": self.env.ref("stock.picking_type_in").id,
                }
            )
            self.env["stock.move"].create(
                {
                    "name": self.product_consu.name,
                    "product_id": self.product_consu.id,
                    "product_uom_qty": 50.000,
                    "product_uom": self.product_consu.uom_id.id,
                    "picking_id": picking.id,
                    "location_id": self.env.ref("stock.stock_location_customers").id,
                    "location_dest_id": self.location.id,
                }
            )
            picking.action_confirm()
            picking.move_ids_without_package.quantity = 50.000
            picking.button_validate()

        snapshot_10 = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-01-01 10:00:00"),
            }
        )
        snapshot_10.action_generate_stock_quant_history()
        self.assertFalse(snapshot_10.stock_quant_history_ids)

    def test_different_uom(self):
        with freeze_time("2023-01-01 10:00:00"):
            self._update_product_stock(10, uom=self.env.ref("uom.product_uom_dozen"))

        snapshot_10 = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-01-01 10:00:00"),
            }
        )
        snapshot_10.action_generate_stock_quant_history()
        quant_history_10 = snapshot_10.stock_quant_history_ids.filtered(
            lambda quant_history,
            pdt=self.product,
            loc=self.location: quant_history.product_id == pdt
            and quant_history.location_id == loc
        )
        self.assertEqual(quant_history_10.quantity, 120)

    def test_default_name(self):
        snapshot = self.env["stock.quant.history.snapshot"].new()
        self.assertEqual(snapshot.name, "Snapshot")
