from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
from datetime import date
import base64


class AgencyWizard(models.TransientModel):
    _name = 'agency.report'
    _description = 'Agency Wizard'

    def _default_start_date(self):
        """Returns the first day of the current month."""
        today = date.today()
        return today.replace(day=1)

    def _default_end_date(self):
        """Returns today's date."""
        return date.today()

    start_date = fields.Date(string='Start Date', required=True, default=_default_start_date)
    end_date = fields.Date(string='End Date', required=True, default=_default_end_date)
    agency_ids = fields.Many2one('res.agency', string="Agency")

    @api.model
    def default_get(self, fields):
        res = super(AgencyWizard, self).default_get(fields)
        return res

    def agency_generate_report(self):
        # Ensure the start date is not after the end date
        if self.start_date > self.end_date:
            raise UserError('Start date cannot be later than end date.')

        company_logo = self.env.company.logo

        # Example: Generate a report based on the date range
        generated_data = self._generate_data(self.start_date, self.end_date, self.agency_ids)
        report_data = {
            'start_date': self.start_date,
            'agency_ids': self.agency_ids.name,
            'end_date': self.end_date,
            'company_logo': company_logo,

            'data': generated_data['report_data'],  # The actual report data returned
            'total_expense_sum': generated_data['total_expense_sum'] + generated_data['total_vendor_sum'],
            # Sum of total_amount_expense
            'total_cash_payment': generated_data['total_cash_payment'],
            'total_bank_payment': generated_data['total_bank_payment'],

        }

        # Return the report data (or print it, save it as PDF, etc.)
        print("vvvcfffffffffffffffffffffffffff", report_data)
        return self.env.ref('saara_spaces_models.agency_report_action_template').report_action(self, data=report_data)

    def _generate_data(self, start_date, end_date, agency_id):
        # Fetch the records from the project.interior model
        today = date.today()
        projects = self.env['project.expenses'].search([
            ('expense_date', '>=', start_date),
            ('expense_date', '<=', end_date),
            ('agency_id', '=', agency_id.id),
        ])
        if not agency_id:
            projects = self.env['project.expenses'].search([
                ('expense_date', '>=', start_date),
                ('expense_date', '<=', end_date),

            ])

        vendor_projects = self.env['vendor.payment.method'].search([
            ('payment_date', '>=', start_date),
            ('payment_date', '<=', end_date),
            ('vendor_id', '=', agency_id.id),
            ('expenses', '=', False),
            ('interior_project_id', '!=', False)
        ])
        if not agency_id:
            vendor_projects = self.env['vendor.payment.method'].search([
                ('payment_date', '>=', start_date),
                ('payment_date', '<=', end_date),
                ('expenses', '=', False),
                ('interior_project_id', '!=', False)
            ])
        print("ddddddddddddddddddddddddddddddddddd", vendor_projects)
        report_data_new = []
        total_expense_sum = 0  # Initialize the sum for total_amount_expense
        total_vendor_sum = 0
        total_cash_payment = 0  # Initialize the sum for cash payments
        total_bank_payment = 0

        for expense in projects:
            project_data = {
                'expenses_ids': [],
            }
            total_expense_sum += expense.total_amount
            if expense.payment_type == 'cash':
                total_cash_payment += expense.total_amount  # Sum cash payments for expense
            elif expense.payment_type == 'bank':
                total_bank_payment += expense.total_amount
            project_data['expenses_ids'].append({
                'agency_id': expense.agency_id.name,
                'project_id': expense.project_id.name,
                'agency_category': expense.agency_category.name,
                'payment_type': expense.payment_type,
                'expense_date': expense.expense_date,
                'type': 'Expense',
                'total_cost': expense.project_id.cost_price,
                'customer_amount': expense.project_id.customer_amount,
                'pending': expense.project_id.balance_receivable,
                'total_amount': expense.project_id.total_paid,
                'total_amount_expense': expense.total_amount,
                'currency_id': expense.currency_id.symbol,
            })
            report_data_new.append(project_data)
        for vendor in vendor_projects:
            for payment_line in vendor.project_form_id:
                project_datav = {
                    'vendor_ids': [],
                }
                total_vendor_sum += payment_line.vendor_payment
                if vendor.name == 'cash':
                    total_cash_payment += payment_line.vendor_payment  # Sum cash payments for vendor
                elif vendor.name == 'bank':
                    total_bank_payment += payment_line.vendor_payment
                project_datav['vendor_ids'].append({
                    'agency_id': vendor.vendor_id.name,
                    'type': 'Debit',
                    'agency_category': payment_line.agency_category.name,
                    'payment_type': vendor.name,
                    'payment_date': vendor.payment_date,
                    'currency_id': vendor.currency_id.symbol,
                    'project_id': payment_line.project_id.name,
                    'total_cost': payment_line.project_id.cost_price,
                    'paid_amount': payment_line.project_id.total_paid,
                    'pending': payment_line.project_id.balance_receivable,
                    'total_amount_vendor': payment_line.vendor_payment,

                })
                report_data_new.append(project_datav)

        return {
            'report_data': report_data_new,
            'total_expense_sum': total_expense_sum,
            'total_vendor_sum': total_vendor_sum,
            'total_cash_payment': total_cash_payment,
            'total_bank_payment': total_bank_payment,
        }
