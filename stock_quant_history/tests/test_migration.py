# Copyright 2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import importlib.util
from pathlib import Path

from odoo import fields
from odoo.modules.module import get_module_path

from odoo.addons.base.tests.common import BaseCommon


class TestStockQuantHistoryMigration(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        migration_path = (
            Path(get_module_path("stock_quant_history"))
            / "migrations"
            / "19.0.1.0.0"
            / "post-migration.py"
        )
        spec = importlib.util.spec_from_file_location(
            "stock_quant_history_post_migration", migration_path
        )
        cls.migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.migration)
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create(
            {"name": "Legacy snapshot company B"}
        )
        cls.location_root = cls.env["stock.location"].create(
            {
                "name": "Legacy snapshot root",
                "usage": "view",
                "company_id": False,
            }
        )
        cls.location_a = cls.env["stock.location"].create(
            {
                "name": "Legacy location A",
                "location_id": cls.location_root.id,
                "usage": "internal",
                "company_id": cls.company_a.id,
            }
        )
        cls.location_b = (
            cls.env["stock.location"]
            .with_company(cls.company_b)
            .create(
                {
                    "name": "Legacy location B",
                    "location_id": cls.location_root.id,
                    "usage": "internal",
                    "company_id": cls.company_b.id,
                }
            )
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Legacy snapshot product",
                "type": "consu",
                "is_storable": True,
            }
        )

    def _history(self, snapshot, location, quantity):
        return (
            self.env["stock.quant.history"]
            .sudo()
            .create(
                {
                    "snapshot_id": snapshot.id,
                    "product_id": self.product.id,
                    "location_id": location.id,
                    "quantity": quantity,
                }
            )
        )

    def test_migration_is_skipped_without_previous_version(self):
        self.assertIsNone(self.migration.migrate(self.env.cr, None))

    def test_empty_snapshot_without_creator_aborts(self):
        snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.from_string("2024-01-01 10:00:00")}
        )
        self.env["stock.quant.history.snapshot"].flush_model()
        self.env.cr.execute(
            "UPDATE stock_quant_history_snapshot SET create_uid = NULL WHERE id = %s",
            (snapshot.id,),
        )

        snapshots = self.migration._legacy_snapshot_data(self.env.cr)
        with self.assertRaisesRegex(
            RuntimeError,
            rf"empty stock quant history snapshot {snapshot.id}",
        ):
            self.migration._split_snapshots(self.env.cr, snapshots)

    def test_history_count_change_aborts(self):
        snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.from_string("2024-01-01 10:00:00")}
        )
        history = self._history(snapshot, self.location_a, 1)

        def delete_history(cr, snapshots, mapping):
            cr.execute(
                "DELETE FROM stock_quant_history WHERE id = %s",
                (history.id,),
            )

        self.patch(
            self.migration,
            "_rebuild_previous_snapshots",
            delete_history,
        )
        with self.assertRaisesRegex(
            RuntimeError,
            "migration changed the number of history rows",
        ):
            self.migration.migrate(self.env.cr, "18.0.1.0.0")

    def test_same_date_snapshots_rebuild_in_creation_order(self):
        snapshot_date = fields.Datetime.from_string("2024-01-01 10:00:00")
        snapshots_model = self.env["stock.quant.history.snapshot"]
        first_snapshot = snapshots_model.create(
            {
                "inventory_date": snapshot_date,
                "state": "generated",
            }
        )
        second_snapshot = snapshots_model.create(
            {
                "inventory_date": snapshot_date,
                "state": "generated",
            }
        )
        snapshots_model.flush_model()

        snapshots = self.migration._legacy_snapshot_data(self.env.cr)
        mapping = {
            (first_snapshot.id, self.company_a.id): first_snapshot.id,
            (second_snapshot.id, self.company_a.id): second_snapshot.id,
        }
        self.migration._rebuild_previous_snapshots(self.env.cr, snapshots, mapping)
        self.env.invalidate_all(flush=False)

        self.assertFalse(first_snapshot.previous_snapshot_id)
        self.assertEqual(second_snapshot.previous_snapshot_id, first_snapshot)

    def test_split_mixed_company_snapshot_without_losing_lines(self):
        previous_a = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2023-12-31 10:00:00"),
                "company_id": self.company_a.id,
                "state": "generated",
            }
        )
        self._history(previous_a, self.location_a, 1)
        mixed_snapshot = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": fields.Datetime.from_string("2024-01-01 10:00:00"),
                "company_id": self.company_a.id,
                "state": "generated",
                "previous_snapshot_id": previous_a.id,
            }
        )
        history_a = self._history(mixed_snapshot, self.location_a, 2)
        temporary_b = self.env["stock.quant.history.snapshot"].create(
            {
                "inventory_date": mixed_snapshot.inventory_date,
                "company_id": self.company_b.id,
                "state": "generated",
            }
        )
        history_b = self._history(temporary_b, self.location_b, 3)
        empty_snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.from_string("2024-01-02 10:00:00")}
        )
        self.env["stock.quant.history"].flush_model()
        self.env["stock.quant.history.snapshot"].flush_model()
        self.env.cr.execute(
            """
            UPDATE stock_quant_history
               SET snapshot_id = %s
             WHERE id = %s
            """,
            (mixed_snapshot.id, history_b.id),
        )
        self.env.cr.execute(
            "DELETE FROM stock_quant_history_snapshot WHERE id = %s",
            (temporary_b.id,),
        )

        before_count = self.env["stock.quant.history"].sudo().search_count([])
        self.migration.migrate(self.env.cr, "18.0.1.0.0")
        self.env.invalidate_all(flush=False)

        migrated_a = self.env["stock.quant.history.snapshot"].browse(mixed_snapshot.id)
        migrated_b = self.env["stock.quant.history.snapshot"].search(
            [
                ("company_id", "=", self.company_b.id),
                ("inventory_date", "=", mixed_snapshot.inventory_date),
            ],
            limit=1,
        )
        self.assertEqual(migrated_a.company_id, self.company_a)
        self.assertEqual(migrated_b.company_id, self.company_b)
        self.assertEqual(history_a.snapshot_id, migrated_a)
        self.assertEqual(history_b.snapshot_id, migrated_b)
        self.assertEqual(history_a.company_id, self.company_a)
        self.assertEqual(history_b.company_id, self.company_b)
        self.assertEqual(migrated_a.previous_snapshot_id, previous_a)
        self.assertFalse(migrated_b.previous_snapshot_id)
        self.assertEqual(empty_snapshot.company_id, self.company_a)
        self.assertEqual(
            self.env["stock.quant.history"].sudo().search_count([]), before_count
        )

    def test_companyless_legacy_history_aborts_with_diagnostic(self):
        shared_location = self.env["stock.location"].create(
            {
                "name": "Ambiguous legacy location",
                "location_id": self.location_root.id,
                "usage": "internal",
                "company_id": False,
            }
        )
        snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.from_string("2024-01-01 10:00:00")}
        )
        history = self._history(snapshot, shared_location, 1)
        self.env["stock.quant.history"].flush_model()
        self.env["stock.quant.history.snapshot"].flush_model()
        with self.assertRaisesRegex(
            RuntimeError,
            rf"snapshot {snapshot.id}: history rows \[{history.id}\]",
        ):
            self.migration._legacy_snapshot_data(self.env.cr)

    def test_snapshot_with_deleted_creator_is_not_skipped(self):
        snapshot = self.env["stock.quant.history.snapshot"].create(
            {"inventory_date": fields.Datetime.from_string("2024-01-01 10:00:00")}
        )
        self._history(snapshot, self.location_a, 1)
        self.env["stock.quant.history"].flush_model()
        self.env["stock.quant.history.snapshot"].flush_model()
        self.env.cr.execute(
            "UPDATE stock_quant_history_snapshot SET create_uid = NULL WHERE id = %s",
            (snapshot.id,),
        )

        snapshots = self.migration._legacy_snapshot_data(self.env.cr)
        self.assertIn(snapshot.id, snapshots)
        self.assertFalse(snapshots[snapshot.id]["creator_company_id"])
        mapping = self.migration._split_snapshots(self.env.cr, snapshots)
        self.assertEqual(mapping[snapshot.id, self.company_a.id], snapshot.id)
