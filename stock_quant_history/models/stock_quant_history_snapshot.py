# Copyright 2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging
from collections import defaultdict

from pytz import timezone

from odoo import _, api, fields, models, tools
from odoo.osv.expression import AND

_logger = logging.getLogger(__name__)


class DefaultDict(defaultdict):
    def __missing__(self, key):
        self[key] = self.default_factory(*key)
        return self[key]


class StockQuantHistorySnapshot(models.Model):
    _name = "stock.quant.history.snapshot"
    _description = "stock.quant.history generation configuration model"
    _order = "inventory_date desc"

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
        help="Base snapshot used to generate this snapshot",
    )

    @api.depends("inventory_date")
    def _compute_name(self):
        # Odoo enforce users to be linked to an active lang
        lang = self.env["res.lang"]._lang_get(self.env.user.lang)
        dt_format = lang.date_format + " " + lang.time_format

        for rec in self:
            if not rec.inventory_date:
                rec.name = _("Snapshot")
                continue

            user_tz = self.env.user.tz or "UTC"
            user_timezone = timezone(user_tz)

            local_inventory_date = rec.inventory_date.astimezone(user_timezone)

            rec.name = _("Snapshot %s") % local_inventory_date.strftime(dt_format)

    def action_generate_stock_quant_history(self):
        for snapshot in self:
            snapshot._generate_stock_quant_history()

    def _prepare_stock_move_line_filter(self, previous_quant_snapshot):
        domain = [
            ("state", "=", "done"),
            ("date", "<=", self.inventory_date),
            ("product_id.type", "=", "product"),
        ]
        if previous_quant_snapshot.exists():
            domain = AND(
                [domain, [("date", ">", previous_quant_snapshot.inventory_date)]]
            )
        return domain

    @api.model
    def _ignored_location_usage(self):
        """If you overwrite or change this
        list you'll probably want to regenerate all your
        snapshots"""
        return [
            "supplier",
            "customer",
            "inventory",
        ]

    def _copy_previous_stock_quant_history(self):
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
        duplicated_fields = ", ".join(self.env["stock.quant.history"]._fields_to_copy())
        _logger.info(
            "SQL Processing %s from %s (copy fields: %s)",
            self.name,
            self.previous_snapshot_id.name,
            duplicated_fields,
        )
        if self.previous_snapshot_id.stock_quant_history_ids.exists():
            _logger.info(
                "Duplicate %s previous stock.quant.history...",
                len(self.previous_snapshot_id.stock_quant_history_ids),
            )
            self.flush()
            self.env.cr.execute(
                "INSERT INTO stock_quant_history ("
                "    snapshot_id,"
                f"    {duplicated_fields}"
                ") SELECT"
                "    %(snapshot_id)s,"
                f"    {duplicated_fields} "
                "FROM"
                "    stock_quant_history "
                "WHERE"
                "    snapshot_id = %(previous_snapshot_id)s",
                dict(
                    snapshot_id=self.id,
                    previous_snapshot_id=self.previous_snapshot_id.id,
                ),
            )
            self.refresh()
        for stock_quant_history in self.sudo().stock_quant_history_ids:
            quant_history[
                (
                    stock_quant_history.product_id,
                    stock_quant_history.lot_id,
                    stock_quant_history.location_id,
                )
            ] = stock_quant_history
        return quant_history

    def _apply_stock_move_lines_group(
        self, quant_history, location_field_name, compute_quantity
    ):
        domain = self._prepare_stock_move_line_filter(self.previous_snapshot_id)
        domain = AND(
            [
                domain,
                [
                    (
                        f"{location_field_name}.usage",
                        "not in",
                        self._ignored_location_usage(),
                    )
                ],
            ]
        )
        for stock_move_line_grouped in self.env["stock.move.line"].read_group(
            domain=domain,
            fields=[
                location_field_name,
                "product_id",
                "lot_id",
                "product_uom_id",
                "qty_done:sum(qty_done)",
            ],
            groupby=[location_field_name, "product_id", "lot_id", "product_uom_id"],
            orderby=f"{location_field_name}, product_id, lot_id",
            lazy=False,
        ):
            lot = (
                self.env["stock.production.lot"]
                .sudo()
                .browse(
                    stock_move_line_grouped["lot_id"][0]
                    if stock_move_line_grouped["lot_id"]
                    else None
                )
            )
            product = (
                self.env["product.product"]
                .sudo()
                .browse(
                    stock_move_line_grouped["product_id"][0]
                    if stock_move_line_grouped["product_id"]
                    else None
                )
            )
            location = (
                self.env["stock.location"]
                .sudo()
                .browse(
                    stock_move_line_grouped[location_field_name][0]
                    if stock_move_line_grouped[location_field_name]
                    else None
                )
            )
            product_uom = (
                self.env["uom.uom"]
                .sudo()
                .browse(
                    stock_move_line_grouped["product_uom_id"][0]
                    if stock_move_line_grouped["product_uom_id"]
                    else None
                )
            ) or product.uom_id
            quantity = product_uom._compute_quantity(
                stock_move_line_grouped["qty_done"], product.uom_id
            )
            stock_quant_history = quant_history[(product, lot, location)]
            stock_quant_history.quantity = tools.float_round(
                compute_quantity(stock_quant_history.quantity, quantity),
                precision_rounding=product.uom_id.rounding,
            )

    def _apply_stock_move_lines(self, quant_history):
        self._apply_stock_move_lines_group(
            quant_history,
            "location_id",
            lambda previous_quantity,
            aggregated_stock_move_line_quantity: previous_quantity
            - aggregated_stock_move_line_quantity,
        )
        self._apply_stock_move_lines_group(
            quant_history,
            "location_dest_id",
            lambda previous_quantity,
            aggregated_stock_move_line_quantity: previous_quantity
            + aggregated_stock_move_line_quantity,
        )

    def _generate_stock_quant_history(self):
        self.ensure_one()
        _logger.info(
            "Starting snapshot at %s...",
            self.inventory_date,
        )
        self.generated_date = fields.Datetime.now()
        previous_quant_snapshot = self.search(
            [
                ("state", "=", "generated"),
                ("inventory_date", "<=", self.inventory_date),
            ],
            order="inventory_date desc",
            limit=1,
        )
        self.previous_snapshot_id = previous_quant_snapshot

        quant_history = self._copy_previous_stock_quant_history()
        self._apply_stock_move_lines(quant_history)

        # remove line with zero to save same disk space
        # avoid loop with direct SQL query
        _logger.info("Remove useless stock_quant_history with quantity == 0")
        # remove line with zero to save same disk space
        # avoid loop with direct SQL query
        _logger.info("Remove useless stock_quant_history with quantity == 0")
        self.env["stock.quant.history"]._flush()
        self.env.cr.execute(
            "DELETE FROM stock_quant_history where quantity = 0 and snapshot_id = %s",
            (self.id,),
        )

        _logger.info("managed picking locks")
        pickings = (
            self.env["stock.move.line"]
            .sudo()
            .search(
                self._prepare_stock_move_line_filter(previous_quant_snapshot),
            )
        ).picking_id
        # Lock all related pickings
        if self.env.company.stock_history_snapshot_auto_locks_picking:
            _logger.info(f"Locking {len(pickings)} related pickings")
            pickings.sudo().write({"is_locked": True})

        _logger.info("Snapshot completed")
        self.state = "generated"

    def action_related_stock_quant_history_tree_view(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_quant_history.action_stock_quant_history"
        )
        action["domain"] = [("snapshot_id", "in", self.ids)]
        return action
