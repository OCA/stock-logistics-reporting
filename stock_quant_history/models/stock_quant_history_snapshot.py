# Copyright 2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging
from collections import defaultdict

from odoo import api, fields, models, tools
from odoo.exceptions import LockError, UserError
from odoo.fields import Domain

_logger = logging.getLogger(__name__)


class DefaultDict(defaultdict):
    def __missing__(self, key):
        self[key] = self.default_factory(*key)
        return self[key]


class StockQuantHistorySnapshot(models.Model):
    _name = "stock.quant.history.snapshot"
    _description = "stock.quant.history generation configuration model"
    _order = "inventory_date desc"
    _check_company_auto = True

    name = fields.Char(
        compute="_compute_name",
    )
    stock_quant_history_ids = fields.One2many(
        comodel_name="stock.quant.history",
        inverse_name="snapshot_id",
        string="Stock quant history",
        help="Generated stock quant history for current snapshot settings.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("generated", "Generated"),
        ],
        string="Status",
        copy=False,
        default="draft",
        readonly=True,
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )

    inventory_date = fields.Datetime(
        string="Inventory date",
        required=True,
        readonly=True,
        help="The date used to create stock.quant.history as it was for the given date",
    )
    generated_date = fields.Datetime(
        string="Generated date",
        readonly=True,
        copy=False,
        help="Date when stock.quant.history line have been created.",
    )
    previous_snapshot_id = fields.Many2one(
        comodel_name="stock.quant.history.snapshot",
        string="Snapshot base",
        readonly=True,
        check_company=True,
        help="Base snapshot used to generate this snapshot",
    )

    @api.depends("inventory_date")
    @api.depends_context("lang", "tz")
    def _compute_name(self):
        # env.lang reflects explicit language overrides from the context.
        lang = self.env["res.lang"]._lang_get(self.env.lang or "en_US")
        dt_format = lang.date_format + " " + lang.time_format

        for rec in self:
            if not rec.inventory_date:
                rec.name = rec.env._("Snapshot")
                continue

            local_inventory_date = fields.Datetime.context_timestamp(
                rec, rec.inventory_date
            )

            rec.name = rec.env._(
                "Snapshot %(date)s",
                date=local_inventory_date.strftime(dt_format),
            )

    def action_generate_stock_quant_history(self):
        self._lock_for_generation()
        for snapshot in self:
            snapshot._generate_stock_quant_history()

    def _lock_and_refresh(self, field_names):
        self.flush_recordset(field_names)
        self.lock_for_update(allow_referencing=True)
        self.invalidate_recordset(field_names, flush=False)

    def _lock_for_generation(self):
        # Preserve state changes already made in this transaction before
        # invalidating the cache to read the value protected by the row lock.
        try:
            self._lock_and_refresh(["state"])
        except LockError:
            raise UserError(
                self.env._("A selected snapshot is already being generated.")
            ) from None
        if any(snapshot.state != "draft" for snapshot in self):
            raise UserError(self.env._("Only draft snapshots can be generated."))

    def write(self, vals):
        if vals:
            try:
                self._lock_and_refresh(["state"])
            except LockError:
                raise UserError(
                    self.env._(
                        "A snapshot cannot be modified while it is being processed."
                    )
                ) from None
            if any(snapshot.state != "draft" for snapshot in self):
                raise UserError(self.env._("Generated snapshots cannot be modified."))
        return super().write(vals)

    def _prepare_stock_move_line_filter(self, previous_quant_snapshot):
        domain = Domain(
            [
                ("state", "=", "done"),
                ("date", "<=", self.inventory_date),
                ("product_id.is_storable", "=", True),
                ("company_id", "=", self.company_id.id),
            ]
        )
        if previous_quant_snapshot.exists():
            domain &= Domain("date", ">", previous_quant_snapshot.inventory_date)
        return domain

    @api.model
    def _allowed_location_usage(self):
        """If you overwrite or change this
        list you'll probably want to regenerate all your
        snapshots"""
        return [
            "internal",
        ]

    def _generate_stock_quant_history(self):
        self.ensure_one()
        self._lock_for_generation()
        self.generated_date = fields.Datetime.now()
        previous_quant_snapshot = self.search(
            [
                ("state", "=", "generated"),
                ("inventory_date", "<=", self.inventory_date),
                ("company_id", "=", self.company_id.id),
            ],
            # Same-date snapshots follow their creation order.
            order="inventory_date desc, id desc",
            limit=1,
        )
        quant_history = DefaultDict(
            lambda product, lot, location: self.env["stock.quant.history"]
            .sudo()
            .create(
                {
                    "snapshot_id": self.id,
                    "product_id": product.id,
                    "lot_id": lot.id,
                    "location_id": location.id,
                    "quantity": 0,
                }
            )
        )
        self.previous_snapshot_id = previous_quant_snapshot

        _logger.info("Processing %s from %s", self.name, self.previous_snapshot_id.name)
        if previous_quant_snapshot.stock_quant_history_ids.exists():
            _logger.info(
                "Duplicate %s previous stock.quant.history...",
                len(previous_quant_snapshot.stock_quant_history_ids),
            )
            for stock_quant_history in previous_quant_snapshot.stock_quant_history_ids:
                # copy is around 3x slower than create !
                quant_copy = quant_history[
                    (
                        stock_quant_history.product_id,
                        stock_quant_history.lot_id,
                        stock_quant_history.location_id,
                    )
                ]
                quant_copy.quantity = stock_quant_history.quantity

        allowed_location_usage = self._allowed_location_usage()
        domain = self._prepare_stock_move_line_filter(previous_quant_snapshot)
        if allowed_location_usage:
            if len(allowed_location_usage) == 1:
                operator = "="
                usage_value = allowed_location_usage[0]
            else:
                operator = "in"
                usage_value = allowed_location_usage

            location_domain = [
                "|",
                ("location_id.usage", operator, usage_value),
                ("location_dest_id.usage", operator, usage_value),
            ]
            domain &= Domain(location_domain)

        stock_move_lines = self.env["stock.move.line"].sudo().search(domain)
        _logger.info(
            "Apply %s stock.move.line since previous snapshot", len(stock_move_lines)
        )
        for move_line in stock_move_lines:
            if move_line.location_id.usage in allowed_location_usage:
                quant_history[
                    (move_line.product_id, move_line.lot_id, move_line.location_id)
                ].quantity = tools.float_round(
                    quant_history[
                        (move_line.product_id, move_line.lot_id, move_line.location_id)
                    ].quantity
                    - move_line.product_uom_id._compute_quantity(
                        move_line.quantity, move_line.product_id.uom_id
                    ),
                    precision_rounding=move_line.product_id.uom_id.rounding,
                )

            if move_line.location_dest_id.usage in allowed_location_usage:
                quant_history[
                    (move_line.product_id, move_line.lot_id, move_line.location_dest_id)
                ].quantity = tools.float_round(
                    quant_history[
                        (
                            move_line.product_id,
                            move_line.lot_id,
                            move_line.location_dest_id,
                        )
                    ].quantity
                    + move_line.product_uom_id._compute_quantity(
                        move_line.quantity, move_line.product_id.uom_id
                    ),
                    precision_rounding=move_line.product_id.uom_id.rounding,
                )
        # remove line with zero to save same disk space
        # avoid loop with direct SQL query
        _logger.info("Remove useless stock_quant_history with quantity == 0")
        history_model = self.env["stock.quant.history"]
        history_model.flush_model(["snapshot_id", "quantity"])
        self.env.cr.execute(
            """
            DELETE FROM stock_quant_history
            WHERE quantity = 0 AND snapshot_id = %s
            RETURNING id
            """,
            (self.id,),
        )
        deleted_history = history_model.browse(
            history_id for (history_id,) in self.env.cr.fetchall()
        )
        deleted_history.invalidate_recordset(flush=False)
        self.invalidate_recordset(["stock_quant_history_ids"], flush=False)
        self.state = "generated"

    def action_related_stock_quant_history_tree_view(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_quant_history.action_stock_quant_history"
        )
        action["domain"] = [("snapshot_id", "in", self.ids)]
        return action
