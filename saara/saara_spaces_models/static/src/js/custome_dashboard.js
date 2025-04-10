/**@odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onMounted } from  "@odoo/owl";
const actionRegistry = registry.category("actions");
import { jsonrpc } from "@web/core/network/rpc_service";

class CustomDashboard extends Component {
    setup() {
        onMounted(() => {
            this.loadChartData();
            this.loadCashFlowChart();
        });
    }

    async loadChartData() {
        const ctx = document.getElementById("agencyPieChart")?.getContext("2d");
        if (!ctx) return;

        try {
            const chartData = await jsonrpc('/project/expenses/chart/data', {});  // 🟢 calling controller
            console.log("=================",chartData)
            const labels = chartData.map(item => item.label);
            const data = chartData.map(item => item.value);
            const colors = ["#3366CC", "#DC3912", "#FF9900", "#109618", "#990099", "#FF6699"];

            new Chart(ctx, {
                type: "pie",
                data: {
                    labels: labels,
                    datasets: [{
                        label: "Agency Wise Expenses",
                        data: data,
                        backgroundColor: colors,
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'right' },
                        title: {
                            display: true,
                            text: "Agency-wise Monthly Expenses"
                        }
                    }
                }
            });
        } catch (error) {
            console.error("Failed to load chart data", error);
        }
    }

    async loadCashFlowChart() {
        const ctx = document.getElementById("cashFlowChart")?.getContext("2d");
        if (!ctx) return;

        try {
            const chartData = await jsonrpc('/cash/flow/chart/data', {});
            const labels = chartData.labels;
            const credits = chartData.credits;
            const debits = chartData.debits;

            new Chart(ctx, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: "Credits",
                            data: credits,
                            borderColor: "lightgreen",
                            fill: false,
                            tension: 0.3,
                        },
                        {
                            label: "Debits",
                            data: debits,
                            borderColor: "orangered",
                            fill: false,
                            tension: 0.3,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' },
                        title: {
                            display: true,
                            text: "Cash Flow"
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return value / 1000 + " K";
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error("Failed to load cash flow chart", error);
        }
    }
}
CustomDashboard.template = "saara_spaces_models.CustomDashboard";
actionRegistry.add("dashboard_tag", CustomDashboard);