This module extends ``stock.picking`` to support the printed flag
mechanism provided by the ``report_printed_flag`` module.

It enables tracking of printed warehouse documents and provides
visibility over report execution in logistics operations.

Main features:

- Adds ``printed`` field to ``stock.picking``
- Tracks printed reports using the core module
- Displays printed report names per record (optional field)
- Provides direct access to printed logs
- Adds search filters:
  - Printed
  - Not Printed
- Adds group by:
  - Printed
  - Printed Report Names
- Supports multi-company configurations

Printed report names are computed from related printed logs and displayed
as a comma-separated string.