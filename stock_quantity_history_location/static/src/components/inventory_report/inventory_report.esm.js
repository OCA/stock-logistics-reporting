/** @odoo-module **/

import {InventoryReportListController} from "@stock/views/list/inventory_report_list_controller";
import {patch} from "@web/core/utils/patch";
const {onWillStart} = owl;

patch(InventoryReportListController.prototype, "inventory_report_list_controller", {
    setup() {
        this._super(...arguments);
        this.multi_location = false;
        onWillStart(async () => {
            this.multi_location = await this.userService.hasGroup(
                "stock.group_stock_multi_locations"
            );
        });
    },
});
