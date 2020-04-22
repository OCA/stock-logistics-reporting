This module uses a wizard to generate a kardex report based on user selected product, location and date range

This report shows the stock of a product in a specific location in a defined time period.

If I generate a report for Product A from 01-01-2020 to 03-01-2020 in location WH/Stock

The report will be the following:

+-----------+---------------------+-----------------+----------+-------------+-----+---------+
| Product   | Date                |  Description    | Origin   | Destination | Qty | Balance |
+-----------+---------------------+-----------------+----------+-------------+-----+---------+
| Product A | 01-01-2020 12:00:00 | Initial Balance |          |             | 100 | 100     |
+-----------+---------------------+-----------------+----------+-------------+-----+---------+
| Product A | 02-01-2020 12:00:00 | PO001           | Vendors  | WH/Stock    | 100 | 200     |
+-----------+---------------------+-----------------+----------+-------------+-----+---------+
| Product A | 02-01-2020 14:00:00 | SO001           | WH/Stock | Customers   | -50 | 150     |
+-----------+---------------------+-----------------+----------+-------------+-----+---------+
| Product A | 02-01-2020 16:30:00 | SO002           | WH/Stock | Customers   | -75 | 75      |
+-----------+---------------------+-----------------+----------+-------------+-----+---------+
| Product A | 03-01-2020 12:00:00 | PO002           | Vendors  | WH/Stock    | 100 | 175     |
+-----------+---------------------+-----------------+----------+-------------+-----+---------+
