from odoo import http
from odoo.http import request
from collections import defaultdict


class ExpenseChartController(http.Controller):

    @http.route('/project/expenses/chart/data', type='json', auth='user')
    def get_expense_data(self):
        data = request.env['project.expenses'].get_expense_chart_data()
        return data

    @http.route('/cash/flow/chart/data', type='json', auth='user')
    def get_cash_flow_data(self):
        # Default dicts to accumulate by year
        credit_by_year = defaultdict(float)
        debit_by_year = defaultdict(float)

        # Get all customer payments (credits)
        credit_records = request.env['payment.method'].search([])
        for record in credit_records:
            if record.payment_date:
                year = record.payment_date.year
                credit_by_year[year] += record.customer_payment

        # Get all vendor payments (debits)
        debit_records = request.env['vendor.payment.method'].search([])
        for record in debit_records:
            if record.payment_date:
                year = record.payment_date.year
                debit_by_year[year] += record.total_payment

        # Collect unique years and sort
        all_years = sorted(set(credit_by_year.keys()) | set(debit_by_year.keys()))

        # Prepare data for chart
        data = {
            'labels': [str(year) for year in all_years],
            'credits': [credit_by_year[year] for year in all_years],
            'debits': [debit_by_year[year] for year in all_years],
        }
        print("====================>>>>>>",data)
        return data
