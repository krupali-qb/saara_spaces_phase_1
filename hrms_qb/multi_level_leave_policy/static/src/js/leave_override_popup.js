/** @odoo-module **/

import { patch } from "@web/core/utils/patch";

(async () => {
    try {
        const { TimeOffDashboard } = await import("@hr_holidays/src/dashboard/time_off_dashboard");
        console.log('222222222222222222222222',TimeOffDashboard)
        patch(TimeOffDashboard.prototype, {
            async loadDashboardData(date = false) {
                await this._super(date);
                const lwpName = "LWP";
                console.log("----------------",lwpName)
                const holidays = this.state.holidays || [];
                const lwp = holidays.find(h => typeof h[0] === 'string' && h[0].toLowerCase().includes(lwpName.toLowerCase()));
                this.state.lwpCount = lwp ? lwp[1] : 0;
            },
        });
    } catch (error) {
        console.warn("TimeOffDashboard patch failed:", error);
    }
})();
