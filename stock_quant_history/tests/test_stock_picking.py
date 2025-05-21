# Copyright 2025 Foodles (https://www.foodles.co/).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from freezegun import freeze_time

from odoo.exceptions import ValidationError
from odoo.tests import tagged, users

from . import common


@tagged("post_install", "-at_install")
@freeze_time("2022-06-01 12:00+00")
class TestStockPickingLock(common.TestStockQuantHistoryCommon):
    """Test the lock constraint functionality on picking.
          ┌────────────────────────┐
          │(unlock, no history) TC3│
          ▼                        │
    ┌───────────┐            ┌─────┴─────┐
    │ Unlocked  ├───────────►│  Locked   │
    └───────────┘ (lock) TC1 └─────┬─────┘
                                   │
    (unlock, history exists) TC2   ▼
                             ┌───────────┐
                             │ Exception │
                             └───────────┘
    """

    def setUp(self):
        super().setUp()
        customer_location = self.env.ref("stock.stock_location_customers")
        # prepare a snapshot
        self.picking = self.env["stock.picking"].create(
            {
                "name": "Test Picking",
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.location.id,
                "location_dest_id": customer_location.id,
                "is_locked": False,
            }
        )
        self.move_line = self.env["stock.move.line"].create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "location_dest_id": customer_location.id,
                "picking_id": self.picking.id,
                "product_uom_id": self.product.uom_id.id,
                "lot_id": self.lot.id,
                "quantity": 1,
            }
        )
        # Force the automatic picking lock setting
        self.env.company.sudo().stock_history_snapshot_auto_locks_picking = True

    @users("stock_manager")
    def test1_lock_unlock_without_history(self):
        """Test the lock functionality."""
        # Assign and confirm the picking to be locked
        self.picking.action_assign()
        self.picking.action_confirm()
        self.picking.button_validate()
        # This picking should be unlocked (no changes on standard behavior)
        self.picking.write({"is_locked": True})
        self.assertTrue(self.picking.is_locked, "The picking should be locked.")
        self.picking.write({"is_locked": False})
        self.assertFalse(
            self.picking.is_locked, "The picking should be unlocked after toggling."
        )

    @users("stock_manager")
    def test2_unlock_with_history(self):
        """Test the unlock functionality with history."""
        # Validate and finish the picking to be locked
        self.picking.action_assign()
        self.picking.action_confirm()
        self.picking.button_validate()
        # Create a snapshot including this picking
        self.stock_history_now.action_generate_stock_quant_history()
        # Try to unlock the picking
        with self.assertRaises(ValidationError):
            self.picking.write({"is_locked": False})

    @users("stock_manager")
    def test3_unlock_with_past_history(self):
        """Test the unlock functionality without history."""
        # Create a snapshot before confirming the picking
        self.stock_history_now.action_generate_stock_quant_history()
        # Validate and finish the picking to be locked
        self.picking.action_assign()
        self.picking.action_confirm()
        self.picking.button_validate()
        self.picking.write({"is_locked": True})
        self.assertTrue(self.picking.is_locked, "The picking should be locked.")
        # This picking should be unlocked (no changes on standard behavior)
        self.picking.write({"is_locked": False})
        self.assertFalse(
            self.picking.is_locked, "The picking should be unlocked after toggling."
        )

    @users("stock_manager")
    def test_lock_done_picking_on_snapshot_creation_with_option(self):
        """Test that the picking is locked when a snapshot is created."""
        # Validate and finish the picking to be locked
        self.picking.action_assign()
        self.picking.action_confirm()
        self.picking.button_validate()
        # Create a snapshot including this picking
        self.stock_history_now.action_generate_stock_quant_history()
        # The picking should be locked after the snapshot creation
        self.assertTrue(
            self.picking.is_locked, "The picking should be locked after snapshot."
        )

    @users("stock_manager")
    def test_lock_done_picking_on_snapshot_creation_no_option(self):
        """Test that the picking is not locked when a snapshot is created without the
        option set (default behavior)."""
        self.env.company.sudo().stock_history_snapshot_auto_locks_picking = False
        # Validate and finish the picking to be locked
        self.picking.action_assign()
        self.picking.action_confirm()
        self.picking.button_validate()
        self.stock_history_now.action_generate_stock_quant_history()
        # The picking should remain unlocked after the snapshot creation
        self.assertFalse(
            self.picking.is_locked, "The picking should remain unlocked after snapshot."
        )

    @users("stock_manager")
    def test_unlocked_pending_picking_on_snapshot_creation(self):
        """Test that the picking remains unlocked when a snapshot is created."""
        # Create a snapshot including this picking
        self.stock_history_now.action_generate_stock_quant_history()
        # The picking should remain unlocked after the snapshot creation
        self.assertFalse(
            self.picking.is_locked, "The picking should remain unlocked after snapshot."
        )

    @users("stock_manager")
    def test_method_get_stock_quant_history_done_picking(self):
        """Test the method to get stock quant history related to a picking."""
        # Create a snapshot including this picking
        self.picking.action_assign()
        self.picking.action_confirm()
        self.picking.button_validate()
        self.stock_history_now.action_generate_stock_quant_history()
        history = self.picking.get_stock_quant_history()
        self.assertTrue(
            history.exists(),
            "The picking should have related stock quant history.",
        )

    @users("stock_manager")
    def test_method_get_stock_quant_history_not_done_picking(self):
        """Test the method to get stock quant history related to a pending picking."""
        self.picking.action_assign()
        self.picking.action_confirm()
        history = self.picking.get_stock_quant_history()
        self.assertFalse(
            history.exists(),
            "The pending picking should not have related stock quant history.",
        )

    @users("stock_manager")
    def test_method_action_toggle_is_locked(self):
        """Test the action to toggle the lock status of a picking."""
        self.picking.action_assign()
        self.picking.action_confirm()
        # No exception should be raised when toggling the lock status
        self.picking.action_toggle_is_locked()
        # Then validate and finish the picking to be locked
        self.picking.button_validate()
        self.stock_history_now.action_generate_stock_quant_history()
        with self.assertRaises(ValidationError):
            self.picking.action_toggle_is_locked()

    def test_method_check_unlock_allowed(self):
        """Test the method to check if a picking can be unlocked."""
        self.picking.action_assign()
        self.picking.action_confirm()
        self.picking.button_validate()
        # Unlock the picking
        self.picking.write({"is_locked": False})
        self.picking.check_unlock_allowed()
        # Create a snapshot including this picking
        self.stock_history_now.action_generate_stock_quant_history()
        with self.assertRaises(ValidationError):
            self.picking.check_unlock_allowed()
