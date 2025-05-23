from odoo import models, fields

class SameDayLeaveWizard(models.TransientModel):
    _name = 'same.day.leave.wizard'
    _description = 'Same-Day Leave Confirmation Wizard'

    leave_id = fields.Many2one('hr.leave', string="Leave", required=True)

    def action_confirm(self):
        self.leave_id.write({'is_same_day_confirmed': True})
        return {'type': 'ir.actions.act_window_close'}

