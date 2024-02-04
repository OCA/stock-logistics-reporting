/** @odoo-module **/

import {Component, onMounted, onWillStart} from "@odoo/owl";
import {download} from "@web/core/network/download";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class report_backend extends Component {
    async start() {
        $(".stock_card_reports_page").html(this.lines.html);
    }

    setup() {
        onWillStart(async () => {
            this.lines = await this.orm.call("report.stock.card.report", "get_html", [
                this.context,
            ]);
        });
        onMounted(async () => {
            this.start();
        });

        this.orm = useService("orm");

        const {active_id, active_model, context, ttype, url} =
            this.props.action.context;
        this.controllerUrl = url;

        this.context = context || {};
        Object.assign(this.context, {
            active_id: active_id || this.props.action.params.active_id,
            model: active_model || false,
            ttype: ttype || false,
        });
    }
    onClickPrint() {
        const data = JSON.stringify(this.lines.html);
        const url = this.controllerUrl
            .replace(":active_id", this.context.active_id)
            .replace(":active_model", this.context.model)
            .replace("output_format", "pdf");
        download({
            data: {data},
            url,
        });
    }
    onClickExport() {
        const data = JSON.stringify(this.lines.html);
        const url = this.controllerUrl
            .replace(":active_id", this.context.active_id)
            .replace(":active_model", this.context.model)
            .replace("output_format", "xlsx");
        download({
            data: {data},
            url,
        });
    }
}
report_backend.template = "report_stock_card_html";
registry.category("actions").add("stock_card_report_backend", report_backend);
