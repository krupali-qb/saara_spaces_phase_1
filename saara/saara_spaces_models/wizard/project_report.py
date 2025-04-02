from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError

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
        # Fetch the records between the start and end dates
        records = self.env['project.expenses'].search([
        ('expense_date', '>=', start_date),
        ('expense_date', '<=', end_date)
    ])
        print("vvvvvvvvvvvvvvvvvvvvvv",records)

        # Process records into a list of dictionaries
        report_data_new = []
        for record in records:
            report_data_new.append({
            'name': record.project_id.name,  # Project Name
            'agency': record.agency_id.name,  # Agency Name
            'amount': record.total_amount,  # Amount
            'payment_type': record.payment_type,  # Payment Type
            'work_category': record.agency_category.name,  # Work Category
            'expense_date': record.expense_date,  # Date
            'currency_id': record.currency_id.symbol
        })

        return report_data_new

