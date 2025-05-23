/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";

export class VendorPaymentMethodController extends FormController {
    setup() {
        super.setup();
        // No ORM service needed for this specific task, but you can initialize it if necessary
    }

    /**
     * Override the `onRecordChanged` method to hide the 'Add a line' button
     * when the project_form_id has 1 or more lines.
     */
    async onRecordChanged(record) {
        console.log("[VendorPaymentMethodController] Record changed:", record);
        await super.onRecordChanged(...arguments);
        this._hideAddLineButton();  // Call the method to hide the "Add a line" button
    }

    /**
     * Custom method to hide the 'Add a line' button in the One2many field.
     */
    _hideAddLineButton() {
        console.log("[VendorPaymentMethodController] Running _hideAddLineButton");

        // Locate the project_form_id field (One2many)
        const lineWidget = this.el.querySelector('[data-name="project_form_id"]');
        if (!lineWidget) {
            console.warn("[VendorPaymentMethodController] Field 'project_form_id' not found in DOM.");
            return;
        }

        // Get the number of lines in the project_form_id field
        const lineCount = this.model.root.data.project_form_id?.length || 0;
        console.log(`[VendorPaymentMethodController] Current line count: ${lineCount}`);

        // Find the "Add a line" button
        const addButton = lineWidget.querySelector('.o_field_one2many_list_row_add');
        if (addButton) {
            // If the line count is greater than or equal to 1, hide the button
            if (lineCount >= 1) {
                addButton.style.display = "none";
                console.log("[VendorPaymentMethodController] Hiding 'Add a line' button (line limit reached).");
            } else {
                // Otherwise, show the "Add a line" button
                addButton.style.display = "";
                console.log("[VendorPaymentMethodController] Showing 'Add a line' button.");
            }
        } else {
            console.warn("[VendorPaymentMethodController] 'Add a line' button not found.");
        }
    }
}

