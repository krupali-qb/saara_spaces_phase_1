from pkg_resources import require

from odoo import fields, models, api


class ProjectExpenses(models.Model):
    _name = "project.expenses"
    _description = 'Project Expenses'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _valid_field_parameter(self, field, name):
        if name == 'tracking':
            return True
        return super()._valid_field_parameter(field, name)

    name = fields.Char(string="Name*", required=True, size=100)
    project_id = fields.Many2one('project.interior', string='Project*', required=True, tracking=True)
    category_id = fields.Many2one('expenses.category', string='Expenses Category*', required=True, tracking=True)
    total_amount = fields.Float(string='Total*', tracking=True, size=25)
    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id)
    agency_id = fields.Many2one('res.agency', string='Agency')
    is_person = fields.Boolean(string='Is Person')
    person_name = fields.Char(string='Person Name')
    paid_by_employee_id = fields.Many2one('res.users', string="Paid By*", required=True, tracking=True)
    payment_type = fields.Selection([('cash', 'Cash'), ('bank', 'Bank')], string='Payment Type*', required=True,
                                    tracking=True)
    expense_date = fields.Date(string='Expense Date*', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Account', default=lambda self: self.env.company)
    notes = fields.Html(string='Notes')
    agency_category = fields.Many2one('agency.category', string="Work Category*", required=True)

    @api.onchange('name', 'person_name')
    def _onchange_fields(self):
        for field in ['name','person_name']:
            value = getattr(self, field)
            if value:
                setattr(self, field, value.title())

    @api.model
    def create(self, vals):
        """Override create method to generate project expense after vendor payment."""
        expenses = super(ProjectExpenses, self).create(vals)
        vendor_payment = self.env['vendor.payment.method'].create({
            'expense_id': expenses.id,
            'interior_project_id': expenses.project_id.id,
            'name': expenses.payment_type,  # Use payment_type (cash/bank)
            'vendor_id': expenses.agency_id.id,
            'payment_date': expenses.expense_date,
            'expenses': True
        })
        # Create records in the One2many project_form_id field
        vendor_payment.write({
            'project_form_id': [(0, 0, {
                'project_id': expenses.project_id.id,
                'agency_category': expenses.agency_category.id,
                'vendor_payment': expenses.total_amount,
            })]
        })
        return expenses

    def write(self, vals):
        res = super(ProjectExpenses, self).write(vals)
        for record in self:
            # Search for related vendor payment records
            vendor_payment_records = self.env['vendor.payment.method'].search([
                ('expense_id.id', '=', record.id),
            ])
            if vendor_payment_records:
                for project_form in vendor_payment_records.mapped('project_form_id'):
                    project_form.write({
                        'vendor_payment': record.total_amount,
                    })
        return res

    def unlink(self):
        for record in self:
            # Find related vendor payment records
            vendor_payment_records = self.env['vendor.payment.method'].search([
            ('expense_id.id', '=', record.id),
            ])
            if vendor_payment_records:
                for vendor_payment in vendor_payment_records:
                    # Delete the project_form_id entries first to avoid constraint violations
                    vendor_payment.project_form_id.unlink()
                    # Delete the vendor payment record itself
                    vendor_payment.unlink()

        return super(ProjectExpenses, self).unlink()

    @api.model
    def get_expense_chart_data(self):
        records = self.read_group(
            domain=[],
            fields=['total_amount:sum'],
            groupby=['agency_category'],
            lazy=False,
        )
        result = []
        for rec in records:
            category_name = self.env['agency.category'].browse(rec['agency_category'][0]).name if rec[
                'agency_category'] else 'Unknown'
            result.append({
                'label': category_name,
                'value': rec['total_amount'],
            })
        print("result================", result)
        return result