To use this module:

1. Install the module.
2. Go to Inventory and open any stock picking.
3. Print a Delivery Slip or Picking Operations report.

If a customer reference exists, it will be displayed in the report.

The module extends the following reports:

- ``stock.report_delivery_document`` (Delivery Slip)
- ``stock.report_picking`` (Picking Operations)

The reference is resolved automatically based on the picking partner.
If no direct reference is found, the system falls back to the commercial
partner reference.
