from odoo import models, fields, api

class EmployeeLwpDashboard(models.Model):
    _name = 'employee.lwp.dashboard'
    _description = 'Employee LWP Dashboard'

    name = fields.Char(string='Dashboard', default='LWP Dashboard')
    lwp_count = fields.Integer(string='LWP Leave Count', compute='_compute_lwp_count')
    user_employee = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['name'] = 'LWP Dashboard'
        return res

    @api.depends('lwp_count')
    def _compute_lwp_count(self):
        for record in self:
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            print("ssssssssssssssssssssssssss",employee)
            if employee:
                lwp_leaves = self.env['hr.leave'].search_count([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id.name', 'ilike', 'LWP'),
                    ('state', '=', 'validate')
                ])
                print("ffffffffffffffffffffff",lwp_leaves)
                record.lwp_count = lwp_leaves
            else:
                record.lwp_count = 0

