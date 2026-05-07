from odoo import models


class StockPicking(models.Model):
    """
    Extension of ``stock.picking`` to integrate with the
    ``report_printed_flag`` infrastructure via the mixin.

    Inheriting ``report.printed.mixin`` provides:
    - ``printed``: Boolean field marking the picking as printed.
    - ``printed_log_ids``: One2many relation to print logs.
    - ``printed_report_names``: Computed comma-separated list of printed
      report names.
    - ``action_view_printed_logs()``: UI action to view logs.

    No additional fields or methods are needed — all behavior comes from
    the mixin.
    """

    _name = "stock.picking"
    _inherit = ["stock.picking", "report.printed.mixin"]
