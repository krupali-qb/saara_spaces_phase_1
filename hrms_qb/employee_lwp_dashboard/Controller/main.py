from odoo import http
from odoo.http import request


class LwpDashboardController(http.Controller):

    @http.route('/lwp_dashboard/data', type='json', auth='user')
    def get_lwp_dashboard_data(self):
        user = request.env.user
        is_hr = user.has_group('multi_level_leave_policy.group_hr')  # HR group check

        if is_hr:
            # For HR: get all employees and their LWP counts
            employees = request.env['hr.employee'].search([])
            employees_lwp_data = []

            for emp in employees:
                leaves = request.env['hr.leave'].search([
                    ('employee_id', '=', emp.id),
                    ('holiday_status_id.name', 'ilike', 'LWP'),
                    ('state', '=', 'validate')
                ])
                total_duration = sum(leave.number_of_days for leave in leaves)
                employees_lwp_data.append({
                    'employee_name': emp.name,
                    'lwp_count': total_duration,
                })

            return {
                'user_name': 'HR - All Employees',
                'employees_lwp': employees_lwp_data,
            }

        # For normal users: show only their own LWP
        employee = request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        lwp_duration = 0
        employee_name = 'No Employee Found'
        if employee:
            employee_name = employee.name
            leaves = request.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id.name', 'ilike', 'LWP'),
                ('state', '=', 'validate')
            ])
            print("----------------------",leaves.number_of_days)
            lwp_duration = sum(leave.number_of_days for leave in leaves)

        return {
            'user_name': employee_name,
            'lwp_count': lwp_duration,
        }
