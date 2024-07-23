from odoo.api import SUPERUSER_ID, Environment


def uninstall_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    report_action = env.ref("stock.action_report_picking", raise_if_not_found=False)
    if report_action:
        report_action.write({"report_name": "stock.report_picking"})
