/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class CustomReports extends Component {
  setup() {
        this.action = useService("action");
    }

    async MonthlyAccountReport() {
        this.action.doAction("saara_spaces_models.action_work_category_report_wizard_new");
    }

    async ProjectReports() {
        this.action.doAction("saara_spaces_models.action_report_wizard_new");
    }

    async AgencyReports() {
        this.action.doAction("saara_spaces_models.action_agency_report_wizard_new");
    }
}

CustomReports.template = "saara_spaces_models.CustomReports";

registry.category("actions").add("reports_tag", CustomReports);





