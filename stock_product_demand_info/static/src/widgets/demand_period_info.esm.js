/*
    Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {Component} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {usePopover} from "@web/core/popover/popover_hook";

export class DemandPeriodInfoGrid extends Component {
    static template = "stock_product_demand_info.DemandPeriodInfoGrid";
    static props = {
        ...standardFieldProps,
        uom_field: {type: String, optional: true},
    };

    get uomFieldName() {
        return this.props.uom_field ?? "uom_id";
    }

    get uomName() {
        const val = this.props.record.data[this.uomFieldName];
        return val?.display_name ?? val;
    }

    get rows() {
        const info = this.props.record.data[this.props.name];
        if (!info || typeof info !== "object") {
            return [];
        }
        return Object.entries(info).filter(
            ([, data]) => data && typeof data === "object" && data.value !== undefined
        );
    }
}

export class DemandPeriodInfoPopoverContent extends DemandPeriodInfoGrid {
    static template = "stock_product_demand_info.DemandPeriodInfoPopoverContent";
    static props = {
        ...DemandPeriodInfoGrid.props,
        close: {type: Function, optional: true},
    };
}

export class ListDemandPeriodInfoField extends DemandPeriodInfoGrid {
    static template = "stock_product_demand_info.DemandPeriodInfoPopoverButton";
    static components = {PopoverContent: DemandPeriodInfoPopoverContent};
    static props = {...DemandPeriodInfoGrid.props};

    setup() {
        this.popover = usePopover(this.constructor.components.PopoverContent, {
            position: "top",
        });
    }

    showPopover(ev) {
        this.popover.open(ev.currentTarget, {
            record: this.props.record,
            name: this.props.name,
            uom_field: this.props.uom_field,
        });
    }
}

export const demandPeriodInfoField = {
    component: DemandPeriodInfoGrid,
    supportedTypes: ["json"],
    extractProps: ({options}) => ({
        uom_field: options?.uom_field,
    }),
};

export const listDemandPeriodInfoField = {
    ...demandPeriodInfoField,
    component: ListDemandPeriodInfoField,
};

registry.category("fields").add("demand_period_info", demandPeriodInfoField);
registry.category("fields").add("list.demand_period_info", listDemandPeriodInfoField);
