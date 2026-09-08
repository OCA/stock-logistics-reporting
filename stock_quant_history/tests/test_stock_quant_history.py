from collections import defaultdict

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import AccessError, LockError, UserError
from odoo.tests import users

from odoo.addons.base.tests.common import BaseCommon


class TestStockQuantHistory(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
            )
        )

        cls.stock_manager_user = cls.env["res.users"].create(
            {
                "name": "foo",
                "login": "stock_manager",
                "email": "foo@bar.com",
                "lang": "en_US",
                "group_ids": [
                    (
                        6,
                        0,
                        (
                            cls.env.ref("base.group_user")
                            | cls.env.ref("stock.group_stock_manager")
                        ).ids,
                    )
                ],
            }
        )
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.location = cls.warehouse.lot_stock_id
        cls.product = cls.env["product.product"].create(
            {
                "name": "test",
                "type": "consu",
                "tracking": "lot",
                "is_storable": True,
            }
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "lot test",
                "product_id": cls.product.id,
                "company_id": cls.warehouse.company_id.id,
            }
        )
        cls.product_consu = cls.env["product.product"].create(
            {
                "name": "test",
                "type": "consu",
            }
        )
        cls.stock_history_now = cls.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.now(),
            }
        )

    def _update_product_stock(self, qty, uom=None):
        lot = self.lot
        location = self.location
        if not uom:
            uom = self.product.uom_id

        qty_in_base_uom = uom._compute_quantity(qty, self.product.uom_id)

        quant = self.env["stock.quant"].search(
            [
                ("product_id", "=", self.product.id),
                ("location_id", "=", location.id),
                ("lot_id", "=", lot.id if lot else False),
            ],
            limit=1,
        )

        if not quant:
            quant = (
                self.env["stock.quant"]
                .with_context(inventory_mode=True)
                .create(
                    {
                        "product_id": self.product.id,
                        "location_id": location.id,
                        "lot_id": lot.id if lot else False,
                        "inventory_quantity": qty_in_base_uom,
                    }
                )
            )
            quant.action_apply_inventory()
            return

        quant.with_context(inventory_mode=True).write(
            {
                "inventory_quantity_auto_apply": qty_in_base_uom,
            }
        )

    @classmethod
    def quants_quantity_group_by(cls, recordset, key):
        """inspired from sale_product_pack PR: gh:oca/product-pack/pull/159"""
        groups = defaultdict(lambda: 0)
        for elem in recordset:
            groups[key(elem)] += elem.quantity
        return groups

    def assertQuantCompare(self, quants, expected_quants):
        """works either with stock.quant or stock.quants.history"""

        def group_key(quant):
            return quant.product_id, quant.lot_id, quant.location_id

        grouped_quants = self.quants_quantity_group_by(quants, group_key)
        grouped_expected_quants = self.quants_quantity_group_by(
            expected_quants, group_key
        )
        errors1 = []
        errors2 = []
        ok = []
        for key, quantity in grouped_quants.items():
            if grouped_expected_quants[key] != quantity:
                errors1.append(
                    f"got {quantity} != Expected {grouped_expected_quants[key]} for"
                    f"{key}: [{key[0].name}, {key[1].name}, {key[2].name}], "
                )
            else:
                ok.append(
                    f"{grouped_expected_quants[key]} for "
                    f"{key}: [{key[0].name}, {key[1].name}, {key[2].name}], "
                    f"is the same {quantity} !"
                )

        for key, quantity in grouped_expected_quants.items():
            if grouped_quants[key] != quantity:
                errors2.append(
                    f"got {grouped_quants[key]} != Expected {quantity} for "
                    f"{key}: [{key[0].name}, {key[1].name}, {key[2].name}], "
                )
        self.assertEqual(
            len(errors1) + len(errors2),
            0,
            "Following diff detected:\n\n".join(errors1)
            + "\n or/and \n "
            + "\n".join(errors2)
            + "\n\nOK records:\n"
            + "\n".join(ok),
        )

    def test_assert_quant_compare_reports_quantity_mismatch(self):
        expected_snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.now()}
        )
        history_model = self.env["stock.quant.history"].sudo()
        common_values = {
            "product_id": self.product.id,
            "lot_id": self.lot.id,
            "location_id": self.location.id,
        }
        quant = history_model.create(
            {**common_values, "snapshot_id": self.stock_history_now.id, "quantity": 1}
        )
        expected_quant = history_model.create(
            {**common_values, "snapshot_id": expected_snapshot.id, "quantity": 2}
        )

        with self.assertRaises(AssertionError):
            self.assertQuantCompare(quant, expected_quant)

    def test_compare_quant(self):
        self.stock_history_now.action_generate_stock_quant_history()
        self.assertQuantCompare(
            self.stock_history_now.stock_quant_history_ids,
            self.env["stock.quant"].search(
                [
                    (
                        "location_id.usage",
                        "in",
                        self.env[
                            "stock.quant.history.snapshot"
                        ]._allowed_location_usage(),
                    ),
                ]
            ),
        )

    @users("stock_manager")
    def test_unlink_snapshot_unlink_related_stock_quant_history_records(self):
        # browse with current user
        self._update_product_stock(10)
        self.stock_history_now.inventory_date = fields.Datetime.now()
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
        self._update_product_stock(10)
        self.stock_history_now.inventory_date = fields.Datetime.now()
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
            "Snapshot 06/15/1984 11:22:32 AM",
        )
        stock_history_now.inventory_date = fields.Datetime.now()
        stock_history_now.action_generate_stock_quant_history()

    def test_generated_snapshot_cannot_be_generated_again(self):
        self.stock_history_now.action_generate_stock_quant_history()
        history_ids = self.stock_history_now.stock_quant_history_ids.ids
        with self.assertRaisesRegex(UserError, "Only draft snapshots"):
            self.stock_history_now.action_generate_stock_quant_history()
        with self.assertRaisesRegex(UserError, "Only draft snapshots"):
            self.stock_history_now._generate_stock_quant_history()
        self.assertEqual(
            self.stock_history_now.stock_quant_history_ids.ids, history_ids
        )

    def test_concurrent_generation_lock_is_reported(self):
        def lock_for_update(*args, **kwargs):
            raise LockError("Concurrent generation")

        self.patch(
            type(self.stock_history_now),
            "lock_for_update",
            lock_for_update,
        )
        with self.assertRaisesRegex(UserError, "already being generated"):
            self.stock_history_now.action_generate_stock_quant_history()
        self.assertEqual(self.stock_history_now.state, "draft")
        self.assertFalse(self.stock_history_now.stock_quant_history_ids)

    def test_generated_snapshot_is_immutable(self):
        self.stock_history_now.action_generate_stock_quant_history()
        original_values = {
            field_name: self.stock_history_now[field_name]
            for field_name in (
                "company_id",
                "inventory_date",
                "generated_date",
                "previous_snapshot_id",
                "state",
            )
        }
        other_company = self.env["res.company"].create(
            {"name": "Immutable snapshot company"}
        )
        other_snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.now()}
        )
        forbidden_values = (
            {"company_id": other_company.id},
            {"inventory_date": fields.Datetime.from_string("2024-01-01 10:00:00")},
            {"generated_date": False},
            {"previous_snapshot_id": other_snapshot.id},
            {"state": "draft"},
        )
        for values in forbidden_values:
            with self.assertRaisesRegex(UserError, "cannot be modified"):
                self.stock_history_now.write(values)
        for field_name, expected_value in original_values.items():
            self.assertEqual(self.stock_history_now[field_name], expected_value)

    def test_draft_snapshot_company_can_be_changed(self):
        snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.now()}
        )
        other_company = self.env["res.company"].create(
            {"name": "Draft snapshot company"}
        )
        snapshot.company_id = other_company
        self.assertEqual(snapshot.company_id, other_company)

    def test_snapshot_change_lock_is_reported(self):
        def lock_for_update(*args, **kwargs):
            raise LockError("Concurrent snapshot processing")

        self.patch(
            type(self.stock_history_now),
            "lock_for_update",
            lock_for_update,
        )
        with self.assertRaisesRegex(UserError, "while it is being processed"):
            self.stock_history_now.inventory_date = fields.Datetime.now()

    def test_multirecord_generation_guard_is_atomic(self):
        self.stock_history_now.action_generate_stock_quant_history()
        draft_snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.now()}
        )
        with self.assertRaisesRegex(UserError, "Only draft snapshots"):
            (
                draft_snapshot | self.stock_history_now
            ).action_generate_stock_quant_history()
        self.assertEqual(draft_snapshot.state, "draft")
        self.assertFalse(draft_snapshot.stock_quant_history_ids)

    def test_empty_allowed_usage_preserves_copied_base(self):
        with freeze_time("2023-01-01 10:00:00"):
            self._update_product_stock(5)
        base_snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.from_string("2023-01-01 10:00:00")}
        )
        base_snapshot.action_generate_stock_quant_history()
        with freeze_time("2023-01-01 20:00:00"):
            self._update_product_stock(9)
        self.patch(
            type(self.env["stock.quant.history.snapshot"]),
            "_allowed_location_usage",
            lambda self: [],
        )
        snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.from_string("2023-01-01 20:00:00")}
        )
        snapshot.action_generate_stock_quant_history()
        history = snapshot.stock_quant_history_ids.filtered(
            lambda line: line.product_id == self.product
            and line.location_id == self.location
        )
        self.assertEqual(history.quantity, 5)

    def test_multiple_allowed_usages_process_both_move_sides(self):
        with freeze_time("2023-01-01 10:00:00"):
            self._update_product_stock(5)
        self.patch(
            type(self.env["stock.quant.history.snapshot"]),
            "_allowed_location_usage",
            lambda self: ["internal", "inventory"],
        )
        snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.from_string("2023-01-01 10:00:00")}
        )
        snapshot.action_generate_stock_quant_history()
        history = snapshot.stock_quant_history_ids.filtered(
            lambda line: line.product_id == self.product
        )
        self.assertEqual(
            set(history.mapped("location_id.usage")), {"internal", "inventory"}
        )
        self.assertEqual(sum(history.mapped("quantity")), 0)

    def test_snapshot_name_uses_context_timezone(self):
        snapshot = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2024-01-01 10:00:00"),
            }
        )
        self.assertEqual(
            snapshot.with_context(tz="America/Toronto").name,
            "Snapshot 01/01/2024 05:00:00 AM",
        )
        self.assertEqual(
            snapshot.with_context(tz="Europe/Paris").name,
            "Snapshot 01/01/2024 11:00:00 AM",
        )

    def test_snapshot_name_uses_context_language(self):
        self.env["res.lang"]._activate_lang("fr_FR")
        snapshot = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2024-06-15 22:00:00"),
            }
        )
        self.assertEqual(
            snapshot.with_context(lang="en_US", tz="UTC").name,
            "Snapshot 06/15/2024 10:00:00 PM",
        )
        self.assertEqual(
            snapshot.with_context(lang="fr_FR", tz="UTC").name,
            "Snapshot 15/06/2024 22:00:00",
        )

    def test_same_date_snapshot_uses_latest_created_base(self):
        snapshot_date = fields.Datetime.from_string("2024-01-01 10:00:00")
        snapshots = self.env["stock.quant.history.snapshot"]
        first_snapshot = snapshots.create({"inventory_date": snapshot_date})
        first_snapshot.action_generate_stock_quant_history()
        second_snapshot = snapshots.create({"inventory_date": snapshot_date})
        second_snapshot.action_generate_stock_quant_history()
        third_snapshot = snapshots.create({"inventory_date": snapshot_date})
        third_snapshot.action_generate_stock_quant_history()

        self.assertEqual(second_snapshot.previous_snapshot_id, first_snapshot)
        self.assertEqual(third_snapshot.previous_snapshot_id, second_snapshot)

    def test_snapshots_and_access_are_company_scoped(self):
        company_a = self.env.company
        company_b = self.env["res.company"].create({"name": "Snapshot company B"})
        warehouse_b = (
            self.env["stock.warehouse"]
            .with_company(company_b)
            .create(
                {
                    "name": "Snapshot warehouse B",
                    "code": "SQHB",
                    "company_id": company_b.id,
                }
            )
        )
        untracked_product = self.env["product.product"].create(
            {
                "name": "Company scoped product",
                "type": "consu",
                "is_storable": True,
            }
        )

        def set_inventory(company, location):
            quant = (
                self.env["stock.quant"]
                .with_company(company)
                .with_context(inventory_mode=True)
                .create(
                    {
                        "product_id": untracked_product.id,
                        "location_id": location.id,
                        "inventory_quantity": 7,
                    }
                )
            )
            quant.action_apply_inventory()

        set_inventory(company_a, self.location)
        set_inventory(company_b, warehouse_b.lot_stock_id)
        snapshot_date = fields.Datetime.now()
        snapshot_a = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": snapshot_date, "company_id": company_a.id}
        )
        snapshot_b = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": snapshot_date, "company_id": company_b.id}
        )
        snapshot_a.action_generate_stock_quant_history()
        snapshot_b.action_generate_stock_quant_history()

        history_a = snapshot_a.stock_quant_history_ids.filtered(
            lambda history: history.product_id == untracked_product
        )
        history_b = snapshot_b.stock_quant_history_ids.filtered(
            lambda history: history.product_id == untracked_product
        )
        self.assertEqual(history_a.location_id, self.location)
        self.assertEqual(history_b.location_id, warehouse_b.lot_stock_id)
        self.assertEqual(history_a.company_id, company_a)
        self.assertEqual(history_b.company_id, company_b)

        snapshot_b_as_manager = snapshot_b.with_user(self.stock_manager_user)
        self.assertFalse(snapshot_b_as_manager.search([("id", "=", snapshot_b.id)]))
        self.assertFalse(
            history_b.with_user(self.stock_manager_user).search(
                [("id", "in", history_b.ids)]
            )
        )
        with self.assertRaises(AccessError):
            snapshot_b_as_manager.unlink()

    def test_shared_location_is_supported(self):
        shared_root = self.env["stock.location"].create(
            {
                "name": "Shared snapshot root",
                "usage": "view",
                "company_id": False,
            }
        )
        shared_location = self.env["stock.location"].create(
            {
                "name": "Shared snapshot location",
                "location_id": shared_root.id,
                "usage": "internal",
                "company_id": False,
            }
        )
        untracked_product = self.env["product.product"].create(
            {
                "name": "Shared location product",
                "type": "consu",
                "is_storable": True,
            }
        )
        quant = (
            self.env["stock.quant"]
            .with_context(inventory_mode=True)
            .create(
                {
                    "product_id": untracked_product.id,
                    "location_id": shared_location.id,
                    "inventory_quantity": 3,
                }
            )
        )
        quant.action_apply_inventory()
        snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.now()}
        )
        snapshot.action_generate_stock_quant_history()
        history = snapshot.stock_quant_history_ids.filtered(
            lambda line: line.product_id == untracked_product
        )
        self.assertEqual(history.location_id, shared_location)
        self.assertFalse(history.location_id.company_id)
        self.assertFalse(history.company_id)

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
                        "in",
                        self.env[
                            "stock.quant.history.snapshot"
                        ]._allowed_location_usage(),
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
        self.assertFalse(snapshot_15.stock_quant_history_ids)
        self.assertFalse(
            self.env["stock.quant.history"].search(
                [("snapshot_id", "=", snapshot_15.id)]
            )
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
                    "product_id": self.product_consu.id,
                    "product_uom_qty": 50.000,
                    "product_uom": self.product_consu.uom_id.id,
                    "picking_id": picking.id,
                    "location_id": self.env.ref("stock.stock_location_customers").id,
                    "location_dest_id": self.location.id,
                }
            )
            picking.action_confirm()
            picking.move_ids.quantity = 50.000
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
