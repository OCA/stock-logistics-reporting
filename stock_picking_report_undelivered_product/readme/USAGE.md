Open a **done** delivery order and print its report with the gear icon
(⚙) *▸ Print ▸ Delivery Slip*. The undelivered quantities are listed in
a table titled **"Remaining quantities not yet delivered:"** (columns
*Product* and *Quantity*, like the standard backorder block), after the
delivered products table.

## All possible cases, one by one

To try them, create a transfer (*Inventory ▸ Operations ▸ Transfers*)
with operation type *Delivery Orders* and two goods products with
*Demand* 50 and 20. Then, case by case:

1.  **Product partially delivered**: set *Quantity* 10 on the first
    product, leave 0 on the second one, click *Validate* and answer *No
    Backorder*. The first product gets a line in the table with its
    remaining quantity (40).
2.  **Product not delivered at all**: in the same report, the second
    product (0 of 20 delivered, its move was cancelled by the *No
    Backorder* answer) gets its own line with the whole quantity (20),
    so the table shows both lines.
3.  **Quantities postponed to a backorder**: in a new delivery order,
    set *Quantity* 20 of 50, click *Validate* and answer *Create
    Backorder*. The module does not list those 30 pending units: the
    standard backorder block of the report already displays them, so
    nothing is repeated.
4.  **Method "Display all undelivered product lines"**: cases 1 and 2
    are listed.
5.  **Method "Display only partially undelivered product lines"**: only
    lines of products that were partially delivered.
6.  **Method "Display only completely undelivered product lines"**: only
    lines of products with nothing delivered.
