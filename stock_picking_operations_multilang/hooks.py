from odoo.api import SUPERUSER_ID, Environment


def uninstall_hook(env):
    envs = Environment(env.cr, SUPERUSER_ID, {})
    report_action = envs.ref("stock.action_report_picking", raise_if_not_found=False)
    if report_action:
        report_action.write({"report_name": "stock.report_picking"})
