from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
from datetime import date

class SameDayLeaveWizard(models.TransientModel):
    _name = 'same.day.leave.wizard'
    _description = 'Same-Day Leave Confirmation Wizard'

    leave_id = fields.Many2one('hr.leave', string="Leave", required=True)

    def action_confirm(self):
        context = self.env.context
        leave_vals = context.get('leave_vals', {})
        leave_vals.update({'is_same_day_confirmed': True})
        leave = self.env['hr.leave'].with_context(bypass_same_day_check=True).create(leave_vals)
        return {'type': 'ir.actions.act_window_close'}
        
class ForceCasualLeaveWizard(models.TransientModel):
    _name = 'force.casual.leave.wizard'
    _description = 'Force Casual Leave Wizard'

    default_leave_id = fields.Many2one('hr.leave', string="Leave")

    def confirm_forceful_leave(self):
        leave = self.default_leave_id
        print("dddfffffffffffffffffffffffff",leave.id)
        leave.write({'forcefully_confirmed': True})
        print("dddfffffffffffffffffffffffff",leave.forcefully_confirmed)
       
