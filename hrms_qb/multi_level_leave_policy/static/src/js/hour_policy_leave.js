/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
const { DateTime, Info } = luxon;

class CustomFormController extends FormController {
    async onWillSaveRecord(record) {
        const recordData = this.model.root.data; // Accessing model data correctly
        const fullLeaveType = recordData?.holiday_status_id?.[1] || "";
        const leaveType = fullLeaveType.split(" (")[0];
        const leaveDateFrom = recordData?.request_date_from;
        const leaveDateTo = recordData?.request_date_to;

        const today = DateTime.now();
        const leaveDateFromStr = leaveDateFrom?.toISODate();
        const todayStr = today.toISODate();

        console.log("Leave Type:", leaveType);
        console.log("Leave Start Date:", leaveDateFromStr);

        // === Case 1: Same-day 7-Hour Policy Leave ===
        if (this.props.resModel === "hr.leave" && leaveType === "7-Hour Policy Leave") {
            console.log("=========")
            if (leaveDateFromStr === todayStr) {
                const confirmed = await new Promise((resolve) => {
                    this.env.services.dialog.add(ConfirmationDialog, {
                        title: "Same-Day Leave Confirmation",
                        body: "You're applying for same-day '7-Hour Policy Leave'. This is allowed only twice per year. Do you want to continue?",
                        confirm: () => resolve(true),
                        cancel: () => resolve(false),
                    });
                });

                if (!confirmed) return false;

                // Updating fields after confirmation
                this.model.root.update({
                    is_same_day_confirmed: true,
                    to_be_continue: true,
                });
            }
        }

        // === Case 2: Casual Leave with less than 4 days' notice ===
        console.log(">>>>>>>>>>>>>>>>>",leaveDateFromStr)
        if (this.props.resModel === "hr.leave" && leaveType === "Casual Leave" && leaveDateFromStr) {
            const leaveDate = DateTime.fromISO(leaveDateFromStr);
            const daysNotice = leaveDate.diff(today, "days").days;
               console.log("=================",leaveDateFromStr)
            if (daysNotice < 4) {
            console.log("=================",daysNotice)
                const confirmed = await new Promise((resolve) => {
                    this.env.services.dialog.add(ConfirmationDialog, {
                        title: "Short Notice - Casual Leave",
                        body: "You're applying for 'Casual Leave' with less than 4 days' notice. Are you sure you want to proceed?",
                        confirm: () => resolve(true),
                        cancel: () => resolve(false),
                    });
                });

                // Log the state before confirming
                console.log("🚀 State before confirmation:", this.model.root.data);

                // Proceed only if confirmed
                if (!confirmed) return false;

                // Log confirmation
                console.log("🚀 User confirmed: ", confirmed);

                // Update model after confirmation
                this.model.root.update({
                    is_same_day_confirmed_cl: true,
                    to_be_continue_cl: true,  // This should set the value to true
                });

                // Log the updated state
                console.log("🚀 Updated context after confirmation:", this.model.root.data);
            }
        }

        return super.onWillSaveRecord(record);
    }

    // This function ensures the boolean value is set to true when the wizard is opened
    async openWizard() {
        // Here, make sure to update the model data as soon as the wizard is opened
        console.log("Opening wizard...");
        
        // Force update the field to true before the wizard is opened
        this.model.root.update({
            to_be_continue_cl: true,
        });
        
        console.log("🚀 Updated before opening wizard:", this.model.root.data);

        // Now proceed with the wizard's logic
        await super.openWizard();
    }
}

// Patch the controller into the registry
const formView = registry.category("views").get("form");
formView.Controller = CustomFormController;

