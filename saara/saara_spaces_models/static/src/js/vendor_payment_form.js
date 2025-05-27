/* @odoo-module */

import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
console.log("======================load")
//console.log("parentRecord==================",this.props.list.resModel)
patch(ListRenderer.prototype, {
    setup() {
        super.setup();
    },

    get showAddRecord() {

        // Custom logic: If model is 'sale.order.line' and count is 1, hide Add a Line
        if (this.props.list.resModel === 'vendor.payment.method.line') {
            const parentRecord = this.props.list.parentRecord;
            console.log("parentRecord==================",parentRecord)
            if (parentRecord && parentRecord.data && parentRecord.data.order_line) {
                const lineCount = parentRecord.data.order_line.length;
                return lineCount < 1;
            }
        }
        return super.showAddRecord;
    }
});