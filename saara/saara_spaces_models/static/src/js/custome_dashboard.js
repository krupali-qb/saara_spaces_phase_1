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
        console.log("=================", chartData);

        const labels = chartData.map(item => item.label);
        const data = chartData.map(item => item.value);
        const colors = this.generateRandomColors(labels.length);

        new Chart(ctx, {
            type: "doughnut",  // Small typo: it should be "doughnut" (not "Doughnut" capital D)
            data: {
                labels: labels,
                datasets: [{
                    label: "Expenses",
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
            plugins: [ChartDataLabels]
        });
    } catch (error) {
        console.error("Failed to load chart data", error);
    }
}
    generateRandomColors(count) {
    const colors = [];
    for (let i = 0; i < count; i++) {
        const color = `hsl(${Math.floor(Math.random() * 360)}, 70%, 60%)`;
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
            type: "bar",  // <<< bar is better for year vs value
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Credits",
                        data: credits,
                        backgroundColor: "lightgreen",
                        borderColor: "green",
                        borderWidth: 1,
                    },
                    {
                        label: "Debits",
                        data: debits,
                        backgroundColor: "lightcoral",
                        borderColor: "red",
                        borderWidth: 1,
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
                                return value / 1000 + "K";
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

        const gradientRevenue = ctx.createLinearGradient(0, 0, 0, 400);
        gradientRevenue.addColorStop(0, "#ff7e00");
        gradientRevenue.addColorStop(1, "#e65c00");

        const gradientExpense = ctx.createLinearGradient(0, 0, 0, 400);
        gradientExpense.addColorStop(0, "#00b3b3");
        gradientExpense.addColorStop(1, "#008080");

        Chart.defaults.borderColor = 'rgba(0, 0, 0, 0.1)';


        new Chart(ctx, {
            type: "bar",  // ✅ valid type
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Revenue",
                        data: revenues,
                        backgroundColor: gradientRevenue,
                        borderRadius: 6,
                        borderSkipped: false,
                        barPercentage: 0.5,
                    },
                    {
                        label: "Expense",
                        data: expenses,
                        backgroundColor: gradientExpense,
                        borderRadius: 6,
                        borderSkipped: false,
                        barPercentage: 0.5,
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
                indexAxis: 'x',  // ✅ horizontal bars
                scales: {
                    x:{
                    title: {
							display: true,
							text: 'Projects' // Name of x-axis
						},
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                console.log('value------------',value)
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
                        backgroundColor: "#009999",
                        borderRadius: 4
                    },
                    {
                        label: "Total Payment",
                        data: totalPayments,
                        backgroundColor: "#cc0052",
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                indexAxis: 'x',
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
                    x:{
                        title: {
                                display: true,
                                text: 'Agency' // Name of x-axis
                            },
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                console.log('<<<<<<<<<<',value)
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