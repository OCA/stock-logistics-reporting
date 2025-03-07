def uninstall_hook(env):
    report_action = env.ref("stock.action_report_picking", raise_if_not_found=False)
    if report_action:
        report_action.write({"report_name": "stock.report_picking"})
