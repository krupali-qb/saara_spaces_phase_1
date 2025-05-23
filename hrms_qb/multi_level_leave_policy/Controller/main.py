from odoo import http
from odoo.http import request
from datetime import date

class LeaveController(http.Controller):

    @http.route('/leave/same_day_7hour_count', type='json', auth='user')
    def get_same_day_7hour_count(self, employee_id):
        year_start = date.today().replace(month=1, day=1)
        leave_type = request.env['hr.leave.type'].search([('name', '=', '7-Hour Policy Leave')], limit=1)
        count = request.env['hr.leave'].sudo().search_count([
            ('employee_id', '=', employee_id),
            ('holiday_status_id', '=', leave_type.id),
            ('is_same_day_confirmed', '=', True),
            ('request_date_from', '>=', year_start),
            ('state', 'not in', ['cancel', 'refuse']),
        ])
        return count

    @http.route('/leave/get_lwp_id', type='json', auth='user')
    def get_lwp_id(self):
        lwp_type = request.env['hr.leave.type'].sudo().search([('name', '=', 'LWP')], limit=1)
        return lwp_type.id if lwp_type else False
