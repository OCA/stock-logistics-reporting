/* eslint-disable no-unused-vars */
odoo.define("stock.InventoryReportLocationListController", function (require) {
    "use strict";

    var core = require("web.core");
    var InventoryReportListController = require("stock.InventoryReportListController");

    var qweb = core.qweb;
    var _t = core._t;

    var InventoryReportLocationListController = InventoryReportListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.context.no_at_date) {
                return;
            }
            if (this.modelName === "stock.quant" && this.$buttons.length) {
                this.$buttons[0].firstElementChild.innerHTML =
                    "Inventory at Date & Location";
            }
        },
    });
});
