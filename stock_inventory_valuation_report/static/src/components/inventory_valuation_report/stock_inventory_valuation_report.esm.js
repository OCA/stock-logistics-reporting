import {Component, markup, onWillStart} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class InventoryValuationReport extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        this.props.given_context = this.props.action.context?.context || {};
        this.props.given_context.active_id =
            this.props.action.context.active_id || this.props.action.params?.active_id;
        this.props.given_context.model =
            this.props.action.context.active_model || false;
        this.props.given_context.ttype = this.props.action.context.ttype || false;

        this.odoo_context = this.props.action.context;

        onWillStart(async () => {
            await this.get_html();
        });
    }

    async get_html() {
        const result = await this.orm.call(
            this.props.given_context.model,
            "get_html",
            [this.props.given_context],
            {context: this.odoo_context}
        );
        this.html = markup(result && result.html ? result.html : "");
    }

    async print() {
        const result = await this.orm.call(
            this.props.given_context.model,
            "print_report",
            [this.props.given_context.active_id, "qweb-pdf"],
            {context: this.odoo_context}
        );
        this.actionService.doAction(result);
    }

    async export() {
        const result = await this.orm.call(
            this.props.given_context.model,
            "print_report",
            [this.props.given_context.active_id, "xlsx"],
            {context: this.odoo_context}
        );
        this.actionService.doAction(result);
    }
}

InventoryValuationReport.template =
    "stock_inventory_valuation_report.InventoryValuationReportBackend";

registry
    .category("actions")
    .add("stock_inventory_valuation_report_backend", InventoryValuationReport);
