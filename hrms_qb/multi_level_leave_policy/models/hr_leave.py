# models/hr_leave.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # Custom fields for approval hierarchy tracking
    reporting_manager_approved = fields.Boolean(string="Reporting Manager Approved", default=False)
    cto_approved = fields.Boolean(string="CTO Approved", default=False)
    hr_approved = fields.Boolean(string="HR Approved", default=False)

    is_emergency = fields.Boolean(string='Emergency Leave', default=False)
    medical_report = fields.Binary(string='Medical Report', attachment=True)
    
   

    @api.model
    def create(self, values):
        leave = super(HrLeave, self).create(values)
        if not leave.supported_attachment_ids:
             if leave.holiday_status_id.name == 'Sick Time Off' and leave.number_of_days >= 2:
                 raise ValidationError("Attachment is required for sick leave of 2 days or more.")
        if leave.holiday_status_id.name == 'Casual Leave' and leave.number_of_days == 1:
            start_date = leave.request_date_from or leave.date_from.date()
            today = fields.Date.today()
            if (start_date - today).days < 7:
                raise ValidationError("Casual Leave (1 Day) must be applied at least 7 calendar days in advance.")
                
        if leave.holiday_status_id.name == 'Casual Leave' and leave.number_of_days >= 2:
            start_date = leave.request_date_from or leave.date_from.date()
            today = fields.Date.today()
            if (start_date - today).days < 15:
                raise ValidationError("Casual Leave (2 Days or More) must be applied at least 15 calendar days in advance.")
                
        if leave.holiday_status_id.name == 'Emergency Leave':
            employee = leave.employee_id
            leave_start = fields.Date.from_string(leave.request_date_from or leave.date_from.date())
            quarter_start_month = ((leave_start.month - 1) // 3) * 3 + 1
            quarter_start = date(leave_start.year, quarter_start_month, 1)
            quarter_end = quarter_start + relativedelta(months=3) - relativedelta(days=1)

            existing_emergency_leaves = self.search_count([
                ('employee_id', '=', employee.id),
                ('holiday_status_id.name', '=', 'Emergency Leave'),
                ('request_date_from', '>=', quarter_start),
                ('request_date_from', '<=', quarter_end),
                ('state', 'not in', ['cancel', 'refuse'])])

            if existing_emergency_leaves > 3:
                raise ValidationError("An employee is allowed a maximum of 3 Emergency Leaves per quarter.")
                
        # 7-Hour Policy Leave – Max 2 times per month, must be manually approved
        if leave.holiday_status_id.name == '7-Hour Policy Leave':
            employee = leave.employee_id
            leave_date = fields.Date.from_string(leave.request_date_from or leave.date_from.date())
            month_start = date(leave_date.year, leave_date.month, 1)
            month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

            leave_count = self.search_count([
                ('employee_id', '=', employee.id),
                ('holiday_status_id.name', '=', '7-Hour Policy Leave'),
                ('request_date_from', '>=', month_start),
                ('request_date_from', '<=', month_end),
                ('state', 'not in', ['cancel', 'refuse'])])

            if leave_count > 2:
                raise ValidationError("An employee may avail the 7-Hour Policy leave only twice per month.")
            
        if leave.holiday_status_id.name in ['Casual Leave', 'Sick Leave', 'Emergency Leave']:
            self._auto_approve_leave(leave)
        self._send_creation_notification(leave)
        return leave
        
        
    def _send_creation_notification(self, leave):
        """Send a notification message when the leave is created"""
        
        # Get the Reporting Manager (Employee's Manager)
        reporting_manager = leave.employee_id.parent_id.user_id
        # Get the CTO from the CTO group
        cto_group = self.env.ref('multi_level_leave_policy.group_cto')
        cto = self.env['res.users'].search([('groups_id', 'in', cto_group.ids)], limit=1)
        # Get HR users from the HR group
        hr_group = self.env.ref('hr.group_hr_user')
        hr_users = self.env['res.users'].search([('groups_id', 'in', hr_group.ids)],limit=1)

        # Create a list of all the partners (employee, reporting manager, CTO, HR)
        partner_ids = [
            leave.employee_id.user_id.partner_id.id,  # Employee
            reporting_manager.partner_id.id,
            cto.partner_id.id,
            hr_users.partner_id.id,  # Reporting Manager
        ]
       
        # Post a message to all relevant users (employee, reporting manager, CTO, HR)
        leave.message_post(
            body=f"A new leave request has been created for {leave.employee_id.name}. "
                 f"Leave from {leave.date_from} to {leave.date_to}",
            partner_ids=partner_ids,  # Send to all relevant partners
            message_type='notification',
            subtype_xmlid='mail.mt_comment'
        )

    def _auto_approve_leave(self, leave):
        if leave.state == 'draft' and leave.date_from - fields.Date.today() <= timedelta(days=2):
            if not leave.reporting_manager_approved and not leave.cto_approved:
                leave.action_approve()
                
    def auto_approve_pending_leaves(self):
        today = fields.Date.today()
        if self.state == 'draft' and self.date_from - fields.Date.today() <= timedelta(days=2):
            if not self.reporting_manager_approved and not self.cto_approved:
                self.action_approve()
                
                
    @api.model
    def auto_approve_pending_leaves_new(self):
        today = fields.Date.from_string('2025-05-11')
        deadline = today + timedelta(days=2)
        # Fetch leaves pending approval, within 2 days from now, and of specific types
        pending_leaves = self.search([
            ('state', '=', 'confirm'),
            ('holiday_status_id.name', 'in', ['Casual Leave', 'Sick Leave', 'Emergency Leave']),
            ('request_date_from', '<=', deadline),
        ])
        for leave in pending_leaves:
            try:
                leave.action_approve(bypass_user_check=True)
                # Optionally, notify user it was auto-approved
                leave.message_post(
                    body="Leave was automatically approved due to no action within the deadline."
                )
            except Exception as e:
                _logger.error(f"Failed to auto-approve leave {leave.id}: {e}")

    def _get_leave_approval_hierarchy(self, leave):
        """Get the approval hierarchy: Reporting Manager (Employee's Manager) → CTO → HR"""
        
        # Use the employee's `parent_id` to get the Reporting Manager (Employee's Manager)
        reporting_manager = leave.employee_id.parent_id.user_id

        # Get the CTO user based on the user group (you can replace 'your_module.group_cto' with the actual group)
        cto_group = self.env.ref('your_module.group_cto')
        cto = self.env['res.users'].search([('groups_id', 'in', cto_group.ids)], limit=1)

        # Get HR user(s) from the HR group
        hr_group = self.env.ref('hr.group_hr_user')
        hr = self.env['res.users'].search([('groups_id', 'in', hr_group.ids)], limit=1)

        return [reporting_manager, cto, hr]

    def action_approve(self, bypass_user_check=False):
        """Override the approve action to enforce the approval hierarchy"""
        cto_group = self.env.ref('multi_level_leave_policy.group_cto')  # Replace with the actual CTO group reference
        cto_user = self.env['res.users'].search([('groups_id', 'in', cto_group.ids)], limit=1)
        hr_group = self.env.ref('multi_level_leave_policy.group_hr')
        hr = self.env['res.users'].search([('groups_id', 'in', hr_group.ids)], limit=1)
        reporting_manager = self.employee_id.parent_id.user_id
        # Step 1: Reporting Manager approval (Employee's Manager)
        if not self.reporting_manager_approved:
            reporting_manager = self.employee_id.parent_id.user_id
            if self.env.user == reporting_manager or self.env.user == hr:
                self.reporting_manager_approved = True
                self.message_post(
            body=f"Leave approved by Reporting Manager: {self.employee_id.name}",
            partner_ids=[reporting_manager.partner_id.id,cto_user.partner_id.id,hr.partner_id.id,self.employee_id.user_id.partner_id.id],
            message_type='notification',
            subtype_xmlid='mail.mt_comment'
        )
            else:
                raise ValidationError(_("You are not authorized to approve this leave as Reporting Manager."))

        # Step 2: CTO approval
        elif self.reporting_manager_approved and not self.cto_approved:
            cto_group = self.env.ref('multi_level_leave_policy.group_cto')  # Replace with the actual CTO group reference
            cto = self.env['res.users'].search([('groups_id', 'in', cto_group.ids)], limit=1)
            if self.env.user == cto or self.env.user == hr or bypass_user_check:
                self.cto_approved = True
                self.message_post(
        body=f"Leave approved by CTO: {self.employee_id.name}",
        partner_ids=[reporting_manager.partner_id.id,cto_user.partner_id.id,hr.partner_id.id,self.employee_id.user_id.partner_id.id],
        message_type='notification',
        subtype_xmlid='mail.mt_comment'
    )
            else:
                raise ValidationError(_("You are not authorized to approve this leave as CTO."))

        # Step 3: HR approval
        elif self.cto_approved and not self.hr_approved:
            hr_group = self.env.ref('multi_level_leave_policy.group_hr')
            hr = self.env['res.users'].search([('groups_id', 'in', hr_group.ids)], limit=1)
            if self.env.user == hr or bypass_user_check:
                self.hr_approved = True
                self.message_post(
        body=f"Leave approved by HR: {self.employee_id.name}",
        partner_ids=[reporting_manager.partner_id.id,cto_user.partner_id.id,hr.partner_id.id,self.employee_id.user_id.partner_id.id],
        message_type='notification',
        subtype_xmlid='mail.mt_comment'
    )
            else:
                raise ValidationError(_("You are not authorized to approve this leave as HR."))

        # Once all approvals are done, mark the leave as approved
        if self.reporting_manager_approved and self.cto_approved and self.hr_approved:
            super(HrLeave, self).action_approve()

'''
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _check_leave_policy_constraints(self):
        for leave in self:
            leave_type = leave.holiday_status_id.name
            days_count = (leave.date_to - leave.date_from).days + 1

            if leave_type == 'Casual Leave':
                if days_count == 1 and (leave.date_from - fields.Date.today()).days < 7:
                    raise ValidationError(_('Casual Leave (1 Day) must be applied 7 days in advance.'))
                elif days_count > 1 and (leave.date_from - fields.Date.today()).days < 15:
                    raise ValidationError(_('Casual Leave (2+ Days) must be applied 15 days in advance.'))

            if leave_type == 'Emergency Leave' and leave.request_date_from and leave.request_date_from > fields.Date.today():
                raise ValidationError(_('Emergency Leave cannot be pre-applied.'))

            if leave_type == 'Sick Leave' and days_count > 2 and not leave.attachment_ids:
                raise ValidationError(_('Medical Report is mandatory for Sick Leave more than 2 days.'))

            if leave_type == '7-Hour Policy Leave':
                month_leaves = self.search_count([
                    ('employee_id', '=', leave.employee_id.id),
                    ('holiday_status_id.name', '=', '7-Hour Policy Leave'),
                    ('state', 'in', ['validate', 'confirm']),
                    ('date_from', '>=', fields.Date.today().replace(day=1)),
                    ('date_from', '<=', fields.Date.today())
                ])
                if month_leaves >= 2:
                    raise ValidationError(_('Only 2 "7-Hour Policy Leaves" allowed per month.'))

    @api.model
    def create(self, vals):
        res = super(HrLeave, self).create(vals)
        res._check_leave_policy_constraints()
        return res

    def write(self, vals):
        res = super(HrLeave, self).write(vals)
        self._check_leave_policy_constraints()
        return res

    @api.model
    def auto_approve_pending_leaves(self):
        today = fields.Date.today()
        leaves = self.search([
            ('approval_stage', 'in', ['team_leader', 'manager']),
            ('state', '=', 'confirm'),
            ('date_from', '!=', False)
        ])

        for leave in leaves:
            if (leave.date_from - today).days <= 2:
                leave.approval_stage = 'approved'
                leave.state = 'validate'
                leave.message_post(body=_("Auto Approved because no action taken within 2 days before leave date."))

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    emergency_leave_quarter = fields.Integer(string='Emergency Leaves This Quarter', default=0)

    @api.model
    def reset_emergency_leaves(self):
        employees = self.search([])
        for employee in employees:
            employee.emergency_leave_quarter = 0'''
