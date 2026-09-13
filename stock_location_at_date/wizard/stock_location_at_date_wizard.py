from datetime import datetime, time

import pytz

from odoo import fields, models
from odoo.tools import SQL


class StockLocationAtDateWizard(models.TransientModel):
    _name = "stock.location.at.date.wizard"
    _description = "Wizard for Location Inventory At Date"

    at_date = fields.Date(
        string="Stock As Of Date",
        required=True,
        default=fields.Date.today,
        help=(
            "Stock quantities and valuation will be calculated up to end-of-day "
            "(23:59:59) on this date in your local timezone."
        ),
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    location_ids = fields.Many2many(
        "stock.location",
        string="Locations",
        domain=[("usage", "in", ["internal", "transit"])],
        help=(
            "Leave empty to include all internal and transit locations. "
            "Sub-locations (child_of) are automatically included."
        ),
    )
    category_ids = fields.Many2many(
        "product.category",
        string="Product Categories",
        help=(
            "Leave empty to include all product categories. "
            "Sub-categories (child_of) are automatically included."
        ),
    )
    product_ids = fields.Many2many(
        "product.product",
        string="Products",
        help="Leave empty to include all products.",
    )

    def action_open_report(self):
        self.ensure_one()
        tz_name = self.env.user.tz or self.env.company.partner_id.tz or "Asia/Dhaka"
        try:
            user_tz = pytz.timezone(tz_name)
        except Exception:
            user_tz = pytz.timezone("Asia/Dhaka")

        local_eod = user_tz.localize(datetime.combine(self.at_date, time(23, 59, 59)))
        utc_cutoff = local_eod.astimezone(pytz.utc).replace(tzinfo=None)

        self.env.cr.execute(
            SQL(
                "DELETE FROM stock_location_at_date_report WHERE create_uid = %s",
                self.env.user.id,
            )
        )

        where_conditions = [
            SQL("sml.state = 'done'"),
            SQL("sml.location_id != sml.location_dest_id"),
            SQL("sml.date <= %s", utc_cutoff),
            SQL("sml.company_id = %s", self.company_id.id),
            SQL("loc.usage IN ('internal', 'transit')"),
        ]

        if self.location_ids:
            loc_domain = [("id", "child_of", self.location_ids.ids)]
            child_location_ids = self.env["stock.location"].search(loc_domain).ids
            where_conditions.append(SQL("loc.id = ANY(%s)", child_location_ids))
        if self.category_ids:
            cat_domain = [("id", "child_of", self.category_ids.ids)]
            child_category_ids = self.env["product.category"].search(cat_domain).ids
            where_conditions.append(SQL("pt.categ_id = ANY(%s)", child_category_ids))
        if self.product_ids:
            where_conditions.append(
                SQL("sml.product_id = ANY(%s)", self.product_ids.ids)
            )

        where_clause = SQL(" AND ").join(where_conditions)

        cost_method_sql = SQL(
            """
            COALESCE(
                pc.property_cost_method->>sml.company_id::text,
                rc.cost_method,
                'standard'
            )
            """
        )

        hist_std_price_sql = SQL(
            """
            COALESCE(
                (
                    SELECT pv.value
                    FROM product_value pv
                    WHERE pv.product_id = sml.product_id
                      AND pv.company_id = sml.company_id
                      AND pv.date <= %s
                    ORDER BY pv.date DESC, pv.id DESC
                    LIMIT 1
                ),
                (pp.standard_price->>sml.company_id::text)::numeric,
                0.0
            )
            """,
            utc_cutoff,
        )

        cost_sql = SQL(
            """
            CASE
                WHEN %(cost_method)s = 'standard' THEN %(hist_std_price)s
                ELSE COALESCE(
                    NULLIF((sm.value / NULLIF(sm.quantity, 0)), 0),
                    %(hist_std_price)s
                )
            END
            """,
            cost_method=cost_method_sql,
            hist_std_price=hist_std_price_sql,
        )

        query = SQL(
            """
            INSERT INTO stock_location_at_date_report (
                create_uid,
                create_date,
                at_date,
                company_id,
                location_id,
                location_complete_name,
                location_usage,
                product_id,
                product_tmpl_id,
                categ_id,
                cost_method,
                uom_id,
                lot_id,
                package_id,
                quantity,
                unit_cost,
                total_value
            )
            SELECT
                %(uid)s AS create_uid,
                NOW() AS create_date,
                %(at_date)s AS at_date,
                sml.company_id AS company_id,
                loc.id AS location_id,
                loc.complete_name AS location_complete_name,
                loc.usage AS location_usage,
                sml.product_id AS product_id,
                pp.product_tmpl_id AS product_tmpl_id,
                pt.categ_id AS categ_id,
                %(cost_method)s AS cost_method,
                pt.uom_id AS uom_id,
                sml.lot_id AS lot_id,
                sml.package_id AS package_id,
                SUM(
                    CASE WHEN sml.location_dest_id = loc.id
                         THEN sml.quantity_product_uom
                         ELSE -sml.quantity_product_uom
                    END
                ) AS quantity,
                %(cost)s AS unit_cost,
                SUM(
                    CASE WHEN sml.location_dest_id = loc.id
                         THEN sml.quantity_product_uom
                         ELSE -sml.quantity_product_uom
                    END
                ) * %(cost)s AS total_value
            FROM stock_move_line sml
            JOIN stock_move sm ON sm.id = sml.move_id
            JOIN product_product pp ON pp.id = sml.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            JOIN product_category pc ON pc.id = pt.categ_id
            JOIN res_company rc ON rc.id = sml.company_id
            JOIN stock_location loc ON loc.id IN (sml.location_id, sml.location_dest_id)
            WHERE %(where)s
            GROUP BY sml.company_id, loc.id, loc.complete_name, loc.usage,
                     sml.product_id, pp.product_tmpl_id, pt.categ_id,
                     pc.property_cost_method, rc.cost_method,
                     pt.uom_id, sml.lot_id, sml.package_id,
                     pp.standard_price, sm.value, sm.quantity
            HAVING SUM(
                CASE WHEN sml.location_dest_id = loc.id
                     THEN sml.quantity_product_uom
                     ELSE -sml.quantity_product_uom
                END
            ) != 0
            """,
            uid=self.env.user.id,
            at_date=self.at_date,
            cost_method=cost_method_sql,
            cost=cost_sql,
            where=where_clause,
        )
        self.env.cr.execute(query)

        formatted_date = self.at_date.strftime("%d %B %Y")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Location Inventory As Of %s", formatted_date),
            "res_model": "stock.location.at.date.report",
            "view_mode": "list,pivot,graph",
            "domain": [("create_uid", "=", self.env.user.id)],
            "context": {
                "search_default_group_by_location": 1,
                "search_default_group_by_product": 1,
            },
            "target": "main",
        }
