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
            this.loadRevenueVsExpenseChart();
            this.loadAgencyPaymentCountChart();
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
            const colors = this.generateRandomColors(labels.length);
            new Chart(ctx, {
            type: "pie",
            data: {
                labels: labels,
                datasets: [{
                    label: data[0],
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
                    },
                    datalabels: {
                        color: '#fff',
                        formatter: (value, context) => {
                            const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(0);
                            return percentage + "%";
                        },
                        font: {
                            weight: 'bold',
                            size: 14,
                        }
                    }
                }
            },
            plugins: [ChartDataLabels]  // 👈 Register the plugin
        });
        } catch (error) {
            console.error("Failed to load chart data", error);
        }
    }
    generateRandomColors(count) {
    const colors = [];
    for (let i = 0; i < count; i++) {
        const color = `hsl(${Math.floor(Math.random() * 360)}, 70%, 70%)`;
        console.log("color==============",color)
        colors.push(color);
    }
    return colors;
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
    async loadRevenueVsExpenseChart() {
    const ctx = document.getElementById("revenueVsExpenseChart")?.getContext("2d");
    if (!ctx) return;
    try {
        const chartData = await jsonrpc('/project/cost/chart/data', {});
        const labels = chartData.map(item => item.name);
        const revenues = chartData.map(item => item.revenue);
        const expenses = chartData.map(item => item.expense);
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Revenue",
                        data: revenues,
                        backgroundColor: "#4CAF50",
                        borderRadius: 4
                    },
                    {
                        label: "Expense",
                        data: expenses,
                        backgroundColor: "#F44336",
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                    title: {
                        display: true,
                        text: "Project-wise Revenue vs Expense"
                    }
                },
                indexAxis: 'y', // 👈 horizontal bars
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value / 1000 + "K";
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error("Failed to load revenue vs expense data", error);
    }
}
    async loadAgencyPaymentCountChart() {
    const ctx = document.getElementById("agencyPaymentCountChart")?.getContext("2d");
    if (!ctx) return;

    try {
        const chartData = await jsonrpc('/agency/payment/count/chart/data', {});

        const labels = chartData.map(item => item.name);
        const totalExpenses = chartData.map(item => item.total_expense);
        const totalPayments = chartData.map(item => item.total_payment);
        const projectInfo = chartData.map(item => item.projects || "");

        if (window.agencyChartInstance) {
            window.agencyChartInstance.destroy();
        }

        window.agencyChartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Total Expense",
                        data: totalExpenses,
                        backgroundColor: "#ff4d4d",
                        borderRadius: 4
                    },
                    {
                        label: "Total Payment",
                        data: totalPayments,
                        backgroundColor: "#4da6ff",
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                indexAxis: 'y',
                plugins: {
                    legend: { position: 'bottom' },
                    title: {
                        display: true,
                        text: "Agency Wise Expense vs Payment"
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const idx = context.dataIndex;
                                const project = projectInfo[idx];
                                return `Projects: ${project}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value >= 1000 ? value / 1000 + 'K' : value;
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error("Failed to load agency chart data", error);
    }
}
}
CustomDashboard.template = "saara_spaces_models.CustomDashboard";
actionRegistry.add("dashboard_tag", CustomDashboard);