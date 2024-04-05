This module allows regenerate stock.quant as it was for a given date.

All stock quant history re-generated for a given date are called snapshot.

To generate the first snapshot this module assume all `stock.move.line`
are present in the database.

Next snapshot is computed based on the previous snapshot present in the database.

