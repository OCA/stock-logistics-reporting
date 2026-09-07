* In Odoo 19.0, stock valuation journal items (`account.move.line`) generated
  directly by stock moves (e.g. manufacturing consumption/output, scrap,
  inventory write-offs to a location with a valuation account) no longer
  track `quantity` (it defaults to 0), so the `account_qty_at_date` and
  `qty_discrepancy` fields were dropped during the initial 19.0 migration.
* They have since been restored, rebuilt from the `quantity` already kept on
  vendor bill and customer invoice lines that post to the stock valuation
  account (`display_type` in `product`/`cogs`), with the sign resolved from
  each line's `balance` since that `quantity` is unsigned. Journal items
  created directly from stock moves (the case above) are not covered by this
  and keep contributing 0 to the accounting quantity, same as native 19.0.
