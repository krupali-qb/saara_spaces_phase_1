from odoo import models, fields, api
from datetime import date, datetime


class ResUsers(models.Model):
    _inherit = 'res.users'

    employment_type = fields.Selection([
        ('intern', 'Intern'),
        ('probation', 'Probation')
    ], string="Employment Type")

    def write(self, vals):
        res = super(ResUsers, self).write(vals)

        employment_type = vals.get('employment_type', None)
        if employment_type is False:
            for user in self:
                # Get linked employee
                employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
                if employee:
                    leave_type = self.env['hr.leave.type'].search([('name', '=', 'Casual Leave')], limit=1)
                    if leave_type:
                        start_date = date.today().replace(month=1, day=1)
                        end_date = date.today().replace(month=12, day=31)
                        # Check if allocation already exists
                        existing_alloc = self.env['hr.leave.allocation'].search([
                            ('employee_id', '=', employee.id),
                            ('holiday_status_id', '=', leave_type.id),
                            ('date_from', '=', start_date),
                            ('date_to', '=', end_date),
                        ], limit=1)

                        if not existing_alloc:
                            self.env['hr.leave.allocation'].create({
                                'name': 'Casual Leave Allocation',
                                'employee_id': employee.id,
                                'holiday_status_id': leave_type.id,
                                'number_of_days': 8,
                                'state': 'confirm',
                                'date_from': start_date,
                                'date_to': end_date,
                            })
        return res


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_users_in_pm_group(self):
        group_pm = self.env.ref('multi_level_leave_policy.group_pm')
        return self.env['res.users'].search([('groups_id', 'in', group_pm.id)])

    project_manager_id = fields.Many2one('res.users', string="Project Manager",
                                         domain=lambda self: [('id', 'in', self.get_users_in_pm_group().ids)])

    @api.model
    def create(self, vals):
        employee = super(HrEmployee, self).create(vals)
        user = employee.user_id

        # Only proceed if user and employment_type exist
        if user and user.employment_type in ['intern', 'probation']:
            # Find leave type for Sick Time Off
            leave_type = self.env['hr.leave.type'].search([('name', '=', 'Sick Time Off')], limit=1)
            if leave_type:
                start_date = date(date.today().year, 1, 1)
                end_date = date(start_date.year, 12, 31)
                # Create leave allocation
                self.env['hr.leave.allocation'].create({
                    'name': 'Sick Leave Allocation',
                    'employee_id': employee.id,
                    'holiday_status_id': leave_type.id,
                    'number_of_days': 8,
                    'state': 'confirm',  # automatically approve
                    'date_from': start_date,
                    'date_to': end_date,
                })
        else:
            leave_types = self.env['hr.leave.type'].search([('name', 'in', ['Casual Leave', 'Sick Time Off'])])
            start_date = date(date.today().year, 1, 1)
            end_date = date(start_date.year, 12, 31)
            for leave in leave_types:
                self.env['hr.leave.allocation'].create({
                    'name': f'{leave.name} Allocation',
                    'employee_id': employee.id,
                    'holiday_status_id': leave.id,
                    'number_of_days': 8,
                    'state': 'confirm',
                    'date_from': start_date,
                    'date_to': end_date,
                })
        return employee
