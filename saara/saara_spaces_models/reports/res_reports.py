from datetime import date, timedelta
from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = 'res.reports'  # Or your custom model

    def action_print_monthly_account_report(self):
        today = date.today()
        start_date = today.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        currency_symbol = self.env.company.currency_id.symbol
        logo = self.env.company.logo.decode('utf-8') if self.env.company.logo else False

        vendor_records = self.env['vendor.payment.method'].search([
            ('payment_date', '>=', start_date),
            ('payment_date', '<=', end_date),
            ('expenses', '=', False),
            ('interior_project_id', '!=', False)
        ])
        customer_records = self.env['payment.method'].search([
            ('payment_date', '>=', start_date),
            ('payment_date', '<=', end_date),
        ])
        expense_records = self.env['project.expenses'].search([
            ('expense_date', '>=', start_date),
            ('expense_date', '<=', end_date),
        ])

        report_data_new = []
        total_vendor_sum = 0
        total_expense_sum = 0
        total_cash_payment = 0
        total_bank_payment = total_received_sum = 0
        total_received_bank_sum = total_received_cash_sum = 0

        for expense in expense_records:
            project_data = {
                'expenses_ids': [],
            }
            total_expense_sum += expense.total_amount
            if expense.payment_type == 'cash':
                total_cash_payment += expense.total_amount
            elif expense.payment_type == 'bank':
                total_bank_payment += expense.total_amount

            project_data['expenses_ids'].append({
                'type': 'Expense',
                'agency_id': expense.agency_id.name,
                'project_id': expense.project_id.name,
                'agency_category': expense.agency_category.name,
                'payment_type': expense.payment_type,
                'expense_date': expense.expense_date,
                'total_cost': expense.project_id.cost_price,
                'customer_amount': expense.project_id.customer_amount,
                'pending': expense.project_id.balance_receivable,
                'total_amount': expense.project_id.total_paid,
                'total_amount_expense': expense.total_amount,
                'currency_id': expense.currency_id.symbol,
                'person_name': expense.person_name,
            })
            report_data_new.append(project_data)
        for vendor in vendor_records:
            for payment_line in vendor.project_form_id:
                project_datav = {
                    'vendor_ids': [],
                }
                total_vendor_sum += payment_line.vendor_payment
                if vendor.name == 'cash':
                    total_cash_payment += payment_line.vendor_payment
                elif vendor.name == 'bank':
                    total_bank_payment += payment_line.vendor_payment

                project_datav['vendor_ids'].append({
                    'type': 'Debit',
                    'agency_id': vendor.vendor_id.name,
                    'project_id': payment_line.project_id.name,
                    'agency_category': payment_line.agency_category.name,
                    'payment_type': vendor.name,
                    'payment_date': vendor.payment_date,
                    'currency_id': vendor.currency_id.symbol,
                    'total_cost': payment_line.project_id.cost_price,
                    'paid_amount': payment_line.project_id.total_paid,
                    'pending': payment_line.project_id.balance_receivable,
                    'total_amount_vendor': payment_line.vendor_payment,
                })
                report_data_new.append(project_datav)
        for customer in customer_records:
            project_data_custom = {
                'custom_ids': [],
            }
            total_received_sum += customer.customer_payment
            if customer.name == 'cash':
                total_received_cash_sum += customer.customer_payment
            elif customer.name == 'bank':
                total_received_bank_sum += customer.customer_payment

            project_data_custom['custom_ids'].append({
                'type': 'Credit',
                'customer_id': customer.customer_id.name,
                'project_id': customer.interior_project_id.name,
                'payment_date': customer.payment_date,
                'payment_type': customer.name,
                'customer_payment': customer.customer_payment,
                'currency_id': customer.currency_id.symbol,
            })
            report_data_new.append(project_data_custom)
        report_data = {
            'start_date': str(start_date),
            'end_date': str(end_date),
            'currency_id': currency_symbol,
            'company_logo': logo,
            'data': report_data_new,
            'total_expense_sum': total_expense_sum + total_vendor_sum,
            'total_vendor_sum': total_vendor_sum,
            'total_received_sum': total_received_sum,
            'total_cash_payment': total_cash_payment,
            'total_bank_payment': total_bank_payment,
            'total_received_cash_sum': total_received_cash_sum,
            'total_received_bank_sum': total_received_bank_sum,
        }
        return self.env.ref('saara_spaces_models.work_category_report_action_template').report_action(
            self, data=report_data
        )

