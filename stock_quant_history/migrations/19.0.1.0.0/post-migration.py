# Copyright 2024 Foodles (https://www.foodles.co/).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from bisect import bisect_left
from collections import defaultdict

from odoo import api

_logger = logging.getLogger(__name__)


def _legacy_snapshot_data(cr):
    cr.execute(
        """
        SELECT snapshot.id,
               snapshot.state,
               snapshot.inventory_date,
               snapshot.previous_snapshot_id,
               snapshot.create_uid,
               creator.company_id,
               history.id,
               location.company_id
          FROM stock_quant_history_snapshot AS snapshot
     LEFT JOIN res_users AS creator ON creator.id = snapshot.create_uid
     LEFT JOIN stock_quant_history AS history
            ON history.snapshot_id = snapshot.id
     LEFT JOIN stock_location AS location ON location.id = history.location_id
      ORDER BY snapshot.id, history.id
        """
    )
    snapshots = {}
    ambiguous = defaultdict(list)
    for (
        snapshot_id,
        state,
        inventory_date,
        previous_snapshot_id,
        create_uid,
        creator_company_id,
        history_id,
        location_company_id,
    ) in cr.fetchall():
        data = snapshots.setdefault(
            snapshot_id,
            {
                "state": state,
                "inventory_date": inventory_date,
                "previous_snapshot_id": previous_snapshot_id,
                "create_uid": create_uid,
                "creator_company_id": creator_company_id,
                "history_by_company": defaultdict(list),
            },
        )
        if not history_id:
            continue
        if not location_company_id:
            ambiguous[snapshot_id].append(history_id)
            continue
        data["history_by_company"][location_company_id].append(history_id)
    if ambiguous:
        details = "; ".join(
            f"snapshot {snapshot_id}: history rows {history_ids}"
            for snapshot_id, history_ids in sorted(ambiguous.items())
        )
        raise RuntimeError(
            "Cannot migrate stock quant history rows whose company cannot be "
            f"identified from their location: {details}"
        )
    return snapshots


def _copy_snapshot(cr, snapshot_id, company_id):
    cr.execute(
        """
        INSERT INTO stock_quant_history_snapshot
                    (state, inventory_date, generated_date,
                     previous_snapshot_id, company_id,
                     create_uid, create_date, write_uid, write_date)
             SELECT state, inventory_date, generated_date,
                    NULL, %s,
                    create_uid, create_date, write_uid, write_date
               FROM stock_quant_history_snapshot
              WHERE id = %s
          RETURNING id
        """,
        (company_id, snapshot_id),
    )
    return cr.fetchone()[0]


def _split_snapshots(cr, snapshots):
    mapping = {}
    for snapshot_id, data in snapshots.items():
        represented_companies = sorted(data["history_by_company"])
        if represented_companies:
            creator_company_id = data["creator_company_id"]
            original_company_id = (
                creator_company_id
                if creator_company_id in represented_companies
                else represented_companies[0]
            )
        else:
            original_company_id = data["creator_company_id"]

        if not original_company_id:
            raise RuntimeError(
                "Cannot migrate empty stock quant history snapshot "
                f"{snapshot_id}: its creator has no company."
            )

        mapping[snapshot_id, original_company_id] = snapshot_id
        cr.execute(
            """
            UPDATE stock_quant_history_snapshot
               SET company_id = %s,
                   previous_snapshot_id = NULL
             WHERE id = %s
            """,
            (original_company_id, snapshot_id),
        )

        for company_id in represented_companies:
            target_snapshot_id = mapping.get((snapshot_id, company_id))
            if not target_snapshot_id:
                target_snapshot_id = _copy_snapshot(cr, snapshot_id, company_id)
                mapping[snapshot_id, company_id] = target_snapshot_id
            history_ids = data["history_by_company"][company_id]
            cr.execute(
                """
                UPDATE stock_quant_history
                   SET snapshot_id = %s
                 WHERE id = ANY(%s)
                """,
                (target_snapshot_id, history_ids),
            )
    return mapping


def _rebuild_previous_snapshots(cr, snapshots, mapping):
    generated_by_company = defaultdict(list)
    for (original_snapshot_id, company_id), snapshot_id in mapping.items():
        snapshot_data = snapshots[original_snapshot_id]
        if snapshot_data["state"] == "generated":
            generated_by_company[company_id].append(
                (
                    snapshot_data["inventory_date"],
                    original_snapshot_id,
                    snapshot_id,
                )
            )
    for candidates in generated_by_company.values():
        candidates.sort()

    for (original_snapshot_id, company_id), snapshot_id in mapping.items():
        original_previous_id = snapshots[original_snapshot_id]["previous_snapshot_id"]
        previous_snapshot_id = mapping.get((original_previous_id, company_id))
        if not previous_snapshot_id:
            candidates = generated_by_company[company_id]
            previous_index = (
                bisect_left(
                    candidates,
                    (
                        snapshots[original_snapshot_id]["inventory_date"],
                        original_snapshot_id,
                        0,
                    ),
                )
                - 1
            )
            previous_snapshot_id = (
                candidates[previous_index][2] if previous_index >= 0 else None
            )
        cr.execute(
            """
            UPDATE stock_quant_history_snapshot
               SET previous_snapshot_id = %s
             WHERE id = %s
            """,
            (previous_snapshot_id, snapshot_id),
        )


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, api.SUPERUSER_ID, {})
    cr = env.cr
    cr.execute("SELECT COUNT(*) FROM stock_quant_history")
    history_count = cr.fetchone()[0]
    snapshots = _legacy_snapshot_data(cr)
    mapping = _split_snapshots(cr, snapshots)
    _rebuild_previous_snapshots(cr, snapshots, mapping)
    cr.execute("SELECT COUNT(*) FROM stock_quant_history")
    migrated_history_count = cr.fetchone()[0]
    if migrated_history_count != history_count:
        raise RuntimeError(
            "Stock quant history migration changed the number of history rows: "
            f"before={history_count}, after={migrated_history_count}."
        )
    _logger.info(
        "Migrated %s stock quant history rows into %s company-scoped snapshots",
        history_count,
        len(mapping),
    )
