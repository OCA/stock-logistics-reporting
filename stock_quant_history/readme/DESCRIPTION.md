This module allows regenerate stock.quant as it was for a given date.

All stock quant history re-generated for a given date are called
snapshot.

Each snapshot belongs to one company. Its base snapshot and stock move
lines are restricted to that company, including when shared stock
locations are involved.

To generate the first snapshot this module assume all stock.move.line
are present in the database.

Next snapshot is computed based on the previous snapshot present in the
database.

Snapshots with the same inventory date are chained in creation order.
The newest previously generated snapshot is used as the base.

Generated snapshots are immutable and cannot be generated a second
time. Create a new snapshot when another stock-history calculation is
needed.

Extensions may override the allowed location usages. An empty allowed
usage list applies no moves; for an incremental snapshot, the copied
base quantities are therefore preserved.
