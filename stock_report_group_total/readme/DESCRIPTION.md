This module shows the totals of the columns *On Hand*, *Free to Use*,
*Incoming*, *Outgoing*, *Forecasted* and *Total Value* on each group of
the stock report (*Inventory > Reporting > Stock*).

These fields are computed (not stored), so Odoo can't aggregate them in
SQL and the group rows are shown empty by default. This module computes
the sum of these fields for the products of each group.
