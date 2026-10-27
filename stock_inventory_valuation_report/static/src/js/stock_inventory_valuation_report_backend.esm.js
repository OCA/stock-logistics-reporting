/* @odoo-module */

import {Component, markup, onMounted, onWillStart, useRef, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

class StockInventoryValuationReportBackend extends Component {
    static template = "stock_inventory_valuation_report.ClientAction";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.rootRef = useRef("root");
        this.state = useState({
            html: markup(""),
        });

        this.given_context = {};
        this.odoo_context = this.props.action.context;

        if (this.props.action.context.context) {
            this.given_context = this.props.action.context.context;
        }

        this.given_context.active_id =
            this.props.action.context.active_id ||
            (this.props.action.params && this.props.action.params.active_id);
        this.given_context.model = this.props.action.context.active_model || false;
        this.given_context.ttype = this.props.action.context.ttype || false;

        onWillStart(async () => {
            await this.getHtml();
        });

        onMounted(() => {
            this.attachEventListeners();
        });
    }

    attachEventListeners() {
        // Los botones vienen del HTML del servidor, necesitamos adjuntar event listeners
        const printBtn = this.rootRef.el.querySelector(
            ".o_stock_inventory_valuation_report_print"
        );
        const exportBtn = this.rootRef.el.querySelector(
            ".o_stock_inventory_valuation_report_export"
        );

        if (printBtn) {
            printBtn.addEventListener("click", this.onClickPrint.bind(this));
        }
        if (exportBtn) {
            exportBtn.addEventListener("click", this.onClickExport.bind(this));
        }
    }

    async getHtml() {
        const result = await this.orm.call(
            this.given_context.model,
            "get_html",
            [this.given_context],
            {context: this.odoo_context}
        );
        this.state.html = markup(result.html || "");
    }

    async onClickPrint(ev) {
        if (ev) {
            ev.preventDefault();
        }
        const result = await this.orm.call(
            this.given_context.model,
            "print_report",
            [this.given_context.active_id, "qweb-pdf"],
            {context: this.odoo_context}
        );
        return this.action.doAction(result);
    }

    async onClickExport(ev) {
        if (ev) {
            ev.preventDefault();
        }
        const result = await this.orm.call(
            this.given_context.model,
            "print_report",
            [this.given_context.active_id, "xlsx"],
            {context: this.odoo_context}
        );
        return this.action.doAction(result);
    }
}

registry
    .category("actions")
    .add(
        "stock_inventory_valuation_report_backend",
        StockInventoryValuationReportBackend
    );
