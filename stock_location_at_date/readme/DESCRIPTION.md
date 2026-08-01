This module adds an instantaneous, location-wise backdated inventory and valuation report calculated as of any historical cutoff date.

It uses an on-demand pre-aggregated session table (`_auto = False`) to eliminate database table bloat and support high-performance Pivot, List, and Graph views.
