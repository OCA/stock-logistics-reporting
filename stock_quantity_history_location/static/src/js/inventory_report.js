odoo.define(
    "stock_quantity_history_location.InventoryReportListController",
    function (require) {
        "use strict";

        const session = require("web.session");
        const InventoryReportListController = require("stock.InventoryReportListController");

        InventoryReportListController.include({
            init: function () {
                this._super.apply(this, arguments);
                this.multi_location = false;
            },
            willStart: function () {
                const sup = this._super(...arguments);
                const user_group = session
                    .user_has_group("stock.group_stock_multi_locations")
                    .then((hasGroup) => {
                        this.multi_location = hasGroup;
                    });
                return Promise.all([sup, user_group]);
            },
        });
    }
);
