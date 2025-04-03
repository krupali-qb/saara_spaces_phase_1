from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
from datetime import date
class ProjectWizard(models.TransientModel):
    _name = 'project.report'
    _description = 'Report Wizard'

    def _default_start_date(self):
        """Returns the first day of the current month."""
        today = date.today()
        return today.replace(day=1)

    def _default_end_date(self):
        """Returns today's date."""
        return date.today()

    start_date = fields.Date(string='Start Date', required=True, default=_default_start_date)
    end_date = fields.Date(string='End Date', required=True, default=_default_end_date)

    @api.model
    def default_get(self, fields):
        res = super(ProjectWizard, self).default_get(fields)
        return res

    def generate_report(self):
        # Ensure the start date is not after the end date
        if self.start_date > self.end_date:
            raise UserError('Start date cannot be later than end date.')

        # Example: Generate a report based on the date range
        report_data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'data': self._generate_data(self.start_date, self.end_date)
        }

        # Return the report data (or print it, save it as PDF, etc.)
        print("vvvcfffffffffffffffffffffffffff",report_data)
        return self.env.ref('saara_spaces_models.project_report_action_template').report_action(self, data=report_data)

    def _generate_data(self, start_date, end_date):
        # Fetch the records from the project.interior model
        today = date.today()
        projects = self.env['project.interior'].search([])

        report_data_new = []
        for project in projects:
            project_data = {
            'project_name': project.name,
             'project_total': project.total_paid,
              'project_ctc': project.total_paid,
                'currency_id': project.currency_id.symbol,
                'customer_amount': project.customer_amount,
                'cost_price': project.cost_price,
            'vendor_payments': [],
            'customer_payments': [],
            'expenses': [],
        }

        # Loop through vendor payments (agency_payment_id)
            for payment in project.agency_payment_id:
                project_data['vendor_payments'].append({
                'payment_method':payment.name,
                'agency_category': payment.agency_category.name,
                'vendor_id': payment.vendor_id.name,
                'payment_date': payment.payment_date,
                'vendor_payment': payment.vendor_payment,
                'currency_id': payment.currency_id.symbol,
            })

            # Loop through customer payments (payments_ids)
            for payment in project.payments_ids:
                project_data['customer_payments'].append({
                'customer_id': payment.customer_id.name,
                'payment_date': payment.payment_date,
                'customer_payment': payment.customer_payment,
                'name': payment.name,
                'currency_id': payment.currency_id.symbol
            })

        # Loop through expenses (expenses_ids)
            for expense in project.expenses_ids:
                project_data['expenses'].append({
                'category_id': expense.category_id.name,
                'agency_id': expense.agency_id.name,
                'expense_date': expense.expense_date,
                'total_amount': expense.total_amount,
                'name': expense.name,
                'work_catg': expense.agency_category.name,
                'payment_type': expense.payment_type,
                'currency_id': expense.currency_id.symbol
            })

            report_data_new.append(project_data)

        return report_data_new
