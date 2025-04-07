from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError

class ProjectWorkCategoryWizard(models.TransientModel):
    _name = 'work.category.report'
    _description = 'Project Work Category Report Wizard'

    def _default_start_date(self):
        """Returns the first day of the current month."""
        today = date.today()
        return today.replace(day=1)

    def _default_end_date(self):
        """Returns today's date."""
        return date.today()

    start_date = fields.Date(string='Start Date', required=True, default=_default_start_date)
    end_date = fields.Date(string='End Date', required=True, default=_default_end_date)
    project_id = fields.Many2one('project.interior', string="Projects")

    @api.model
    def default_get(self, fields):
        res = super(ProjectWorkCategoryWizard, self).default_get(fields)
        return res

    def work_category_generate_report(self):
        # Ensure the start date is not after the end date
        if self.start_date > self.end_date:
            raise UserError('Start date cannot be later than end date.')
            
        company_logo = self.env.company.logo

        # Example: Generate a report based on the date range
        report_data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'project': self.project_id.name,
            'company_logo': company_logo,
            'data': self._generate_data(self.start_date, self.end_date, self.project_id.name)
        }

        # Return the report data (or print it, save it as PDF, etc.)
        print(">>>>>>>>>>>>>>>>>>", report_data)
        return self.env.ref('saara_spaces_models.work_category_report_action_template').report_action(self, data=report_data)

    def _generate_data(self, start_date, end_date, project):
        # Fetch the records between the start and end dates
        records = self.env['project.interior'].search([
            ('create_date', '>=', start_date),
            ('create_date', '<=', end_date),
            ('name', '=', project)
        ])
        print("----------------------", records.expenses_ids)

        # Process records into a list of dictionaries
        report_data_new = []
        if records:
            print("1111111111111111if")
            for record in records.expenses_ids:
                print("===recordagency_category.name=====",record.agency_category.name)
                report_data_new.append({
                    'name': record.name,  # Project Name
                    # 'agency': record.agency_id.name,  # Agency Name
                    # 'amount': record.total_amount,  # Amount
                    # 'payment_type': record.payment_type,  # Payment Type
                    # 'work_category': record.agency_category.name,  # Work Category
                    # 'expense_date': record.expense_date,  # Date
                    # 'currency_id': record.currency_id.symbol
                })
        else:
            print("222222222222else")
            results= self.env['project.interior'].search([
                ('create_date', '>=', start_date),
                ('create_date', '<=', end_date)])
            print("--------results-----------",results)
            for res in results:
                report_data_new.append({
                    'name' : res.name
                })
            print("report_data_new==================",report_data_new)
            return report_data_new
