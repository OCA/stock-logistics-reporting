As is, this module has no actual effect on the report, but it adds the possibility to alter the lines' order
in the `report_picking` report by overriding the following two methods in a custom module:
* `get_moves_for_report_picking` in the model `stock.picking`; and
* `get_move_lines_for_report_picking` in the model `stock.move`.

These also could be used to filter the moves and move lines in the report, if needed.
