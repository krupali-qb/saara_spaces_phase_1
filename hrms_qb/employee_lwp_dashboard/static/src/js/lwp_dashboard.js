/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class LwpDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            lwp_count: 0,
            user_name: '',
            employees_lwp: [], // for HR: list of employees with LWP count
            is_hr: false,
        });

        onWillStart(async () => {
            const result = await this.rpc("/lwp_dashboard/data");
            if (result.employees_lwp) {
                // HR user case
                this.state.is_hr = true;
                this.state.user_name = result.user_name;
                this.state.employees_lwp = result.employees_lwp;
            } else {
                // Normal user case
                this.state.is_hr = false;
                this.state.user_name = result.user_name;
                this.state.lwp_count = result.lwp_count;
            }
        });
    }
}

LwpDashboard.template = "employee_lwp_dashboard.LwpDashboard";

registry.category("actions").add("employee_lwp_dashboard.lwp_action", LwpDashboard);
