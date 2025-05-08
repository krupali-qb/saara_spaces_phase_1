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
        return data

    @http.route('/project/cost/chart/data', type='json', auth='user')
    def project_cost_chart_data(self):
        records = request.env['project.interior'].search([])
        result = []

        for rec in records:
            result.append({
                'name': rec.name,
                'revenue': rec.customer_amount,
                'expense': rec.total_expenses_amount,
            })
        return result

    @http.route('/agency/payment/count/chart/data', type='json', auth='user')
    def get_agency_expense_and_payment_data(self):
        vendor_data = defaultdict(lambda: {
            'name': '',
            'total_expense': 0.0,
            'total_payment': 0.0,
            'projects': set(),
        })

        # Fetch Vendor Payments
        payment_records = request.env['vendor.payment.method'].search([])
        for rec in payment_records:
            vendor_id = rec.vendor_id.id
            vendor_data[vendor_id]['name'] = rec.vendor_id.name
            vendor_data[vendor_id]['total_payment'] += rec.vendor_payment
            if rec.interior_project_id:
                vendor_data[vendor_id]['projects'].add(rec.interior_project_id.name)

        # Fetch Expenses
        expense_records = request.env['project.expenses'].search([])
        for exp in expense_records:
            vendor_id = exp.agency_id.id
            if vendor_id:  # only if linked to a vendor
                vendor_data[vendor_id]['name'] = exp.agency_id.name
                vendor_data[vendor_id]['total_expense'] += exp.total_amount
                if exp.project_id:
                    vendor_data[vendor_id]['projects'].add(exp.project_id.name)

        # Format Result
        result = []
        for data in vendor_data.values():
            if data['name']:
                result.append({
                    'name': data['name'],
                    'projects': ', '.join(data['projects']),
                    'total_expense': data['total_expense'],
                    'total_payment': data['total_payment'],
                })
        return result
