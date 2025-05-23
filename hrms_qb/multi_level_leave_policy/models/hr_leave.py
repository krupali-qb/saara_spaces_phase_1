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
    is_same_day_confirmed = fields.Boolean(string="Same Day Confirmed")
    is_same_day_confirmed_cl = fields.Boolean(string="Same Day Confirmed")
    forcefully_confirmed = fields.Boolean(string="Forcefully Confirmed", default=False)
    to_be_continue = fields.Boolean("To Be Continued")
    to_be_continue_cl = fields.Boolean('To Be Continued CL')

    def action_refuse(self):
        res = super(HrLeave, self).action_refuse()

        for leave in self:
            # Get users
            employee_user = leave.employee_id.user_id
            reporting_manager = leave.employee_id.parent_id.user_id
            cto_group = self.env.ref('multi_level_leave_policy.group_cto')
            cto = self.env['res.users'].search([('groups_id', 'in', cto_group.ids)], limit=1)
            hr_group = self.env.ref('multi_level_leave_policy.group_hr')
            hr_user = self.env['res.users'].search([('groups_id', 'in', hr_group.ids)], limit=1)
            pm_group = self.env.ref('multi_level_leave_policy.group_pm')
            pm_user = self.env['res.users'].search([('groups_id', 'in', pm_group.ids)], limit=1)

            # Safe partner_id list
            partner_ids = list(filter(None, [
                employee_user.partner_id.id if employee_user and employee_user.partner_id else None,
                reporting_manager.partner_id.id if reporting_manager and reporting_manager.partner_id else None,
                cto.partner_id.id if cto and cto.partner_id else None,
                hr_user.partner_id.id if hr_user and hr_user.partner_id else None,
                pm_user.partner_id.id if pm_user and pm_user.partner_id else None,
            ]))

            # Post message
            leave.message_post(
                body=f"Leave request for {leave.employee_id.name} from {leave.date_from} to {leave.date_to} has been refused by {self.env.user.name}.",
                partner_ids=partner_ids,
                message_type='notification',
                subtype_xmlid='mail.mt_comment'
            )

        return res

    def action_submit_leave_with_check(self):
        self.ensure_one()
        leave = self
        today = fields.Date.today()
        leave_type = leave.holiday_status_id
        employee = leave.employee_id
        leave_date = leave.request_date_from or leave.date_from.date()

        if leave_type.name != 'Casual Leave':
            return self.action_confirm()

        days_diff = (leave_date - today).days
        forceful_needed = (
                (leave.number_of_days == 1 and days_diff < 7) or
                (leave.number_of_days >= 2 and days_diff < 15)
        )

        if forceful_needed and not leave.forcefully_confirmed:
            current_year = today.year
            forceful_count = self.search_count([
                ('employee_id', '=', employee.id),
                ('holiday_status_id.name', '=', 'Casual Leave'),
                ('forcefully_confirmed', '=', True),
                ('request_date_from', '>=', f'{current_year}-01-01'),
                ('request_date_from', '<=', f'{current_year}-12-31'),
                ('state', 'not in', ['cancel', 'refuse']),
            ])
            print("ddddddddddddddddddddddddddddddd", forceful_count)
            if forceful_count > 1:
                self.write({"state": "draft"})
                print("fffffffffffffffffffffffffffffff", self.state)
                raise ValidationError(
                    "You have already used your 2 forceful casual leave overrides this year.Other Casual Leave (1 Day): Must be applied 5 days working hours in advance OR Casual Leave (2 Days or More): Must be applied 15 days in advance")

            # Launch wizard to confirm override
            return {
                'type': 'ir.actions.act_window',
                'name': 'Force Casual Leave Confirmation',
                'res_model': 'force.casual.leave.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_default_leave_id': self.id
                }
            }

        return

    @api.model
    def create(self, vals):
        # Bypass check when coming from wizard or system
        leave_date_from = vals.get('request_date_from')
        holiday_status = vals.get('holiday_status_id')

        if holiday_status and leave_date_from:
            holiday_status_record = self.env['hr.leave.type'].browse(holiday_status)
            if holiday_status_record.name == "Casual Leave":
                # Convert leave date from to datetime object
                leave_date_from = fields.Datetime.from_string(leave_date_from)
                today = fields.Datetime.now()

                # Calculate the difference in days
                days_diff = (leave_date_from - today).days

                # If leave is requested less than 4 days in advance, set the boolean to True
                if days_diff < 4:
                    vals['to_be_continue_cl'] = True
                else:
                    vals['to_be_continue_cl'] = False

        # print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",self.to_be_continue_cl,vals.get("to_be_continue_cl"))
        if self.env.context.get('bypass_same_day_check'):
            return super(HrLeave, self).create(vals)

        leave = super(HrLeave, self).create(vals)
        today = fields.Date.today()

        leave_type = leave.holiday_status_id
        employee = leave.employee_id
        leave_date = leave.request_date_from or leave.date_from.date()

        if leave.holiday_status_id.name == 'Casual Leave':
            today = fields.Date.today()
            start_date = leave.request_date_from or leave.date_from.date()
            day_diff = (start_date - today).days

            # Enforce rules (backend)
            print("dddddddddddddddddddddddddddddddddddddddddddd", vals['to_be_continue_cl'], self.to_be_continue_cl)
            if leave.number_of_days == 1 and day_diff < 7 and vals.get("to_be_continue_cl") == False:
                raise ValidationError(_("Casual Leave (1 Day) must be applied at least 7 calendar days in advance."))
            elif leave.number_of_days >= 2 and day_diff < 15 and vals.get("to_be_continue_cl") == False:
                raise ValidationError(
                    _("Casual Leave (2 Days or More) must be applied at least 15 calendar days in advance."))

            # Max 2 CLs per year
            current_year = today.year
            cl_count = self.search_count([
                ('employee_id', '=', leave.employee_id.id),
                ('holiday_status_id', '=', leave.holiday_status_id.id),
                ('request_date_from', '>=', f'{current_year}-01-01'),
                ('request_date_from', '<=', f'{current_year}-12-31'),
                ('state', '!=', 'refused'),
            ])
            if cl_count > 2:
                raise ValidationError(_("You can only apply for 'Casual Leave' a maximum of 2 times per year."))

        # 🚑 Sick Leave (Attachment Required)
        if leave_type.name == 'Sick Time Off' and leave.number_of_days >= 2 and not leave.supported_attachment_ids:
            raise ValidationError("Attachment is required for sick leave of 2 days or more.")

        if leave_type.name == 'Emergency Leave':
            quarter_start_month = ((leave_date.month - 1) // 3) * 3 + 1
            quarter_start = date(leave_date.year, quarter_start_month, 1)
            quarter_end = quarter_start + relativedelta(months=3) - relativedelta(days=1)
            existing_emergency_leaves = self.search_count([
                ('employee_id', '=', employee.id),
                ('holiday_status_id.name', '=', 'Emergency Leave'),
                ('request_date_from', '>=', quarter_start),
                ('request_date_from', '<=', quarter_end),
                ('state', 'not in', ['cancel', 'refuse']),
            ])
            if existing_emergency_leaves > 1:
                raise ValidationError("An employee is allowed only 1 Emergency Leave per quarter.")

        # ⏱️ 7-Hour Policy Leave: 2 per month, special rules
        if leave_type.name == '7-Hour Policy Leave':
            # Monthly limit
            month_start = date(leave_date.year, leave_date.month, 1)
            month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
            monthly_leaves = self.search_count([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', leave_type.id),
                ('request_date_from', '>=', month_start),
                ('request_date_from', '<=', month_end),
                ('state', 'not in', ['cancel', 'refuse']),
            ])

            if monthly_leaves > 2:
                raise ValidationError("An employee may avail the 7-Hour Policy Leave only twice per month.")

            # Same-day logic
            if leave_date == today:
                #     if not leave.is_same_day_confirmed:
                #         raise ValidationError("Same-day 7-Hour Policy Leave must be confirmed via the wizard.")
                #
                #     # Only 2 confirmed same-day 7-hour leaves per year
                year_start = date(leave_date.year, 1, 1)
                year_end = date(leave_date.year, 12, 31)
                same_day_yearly_leaves = self.search_count([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', leave_type.id),
                    # ('request_date_from', '=', today),
                    ('to_be_continue', '=', True),
                    ('request_date_from', '>=', year_start),
                    ('request_date_from', '<=', year_end),
                    ('state', 'not in', ['cancel', 'refuse']),
                ])
                print("=======same_day_yearly_leaves================", same_day_yearly_leaves)
                if same_day_yearly_leaves >= 2:
                    print("==============>>>>>>>>>>>>>>>>>>>>============")
                    raise ValidationError("Same-day 7-Hour Policy Leave is allowed only twice per year.")

        # Auto-approval for some leave types
        if leave_type.name in ['Casual Leave', 'Sick Leave', 'Emergency Leave']:
            self._auto_approve_leave(leave)
        # Notify
        self._send_creation_notification(leave)

        return leave

    def open_same_day_leave_wizard(self):
        self.ensure_one()
        return {
            'name': 'Confirm Same-Day Leave',
            'type': 'ir.actions.act_window',
            'res_model': 'same.day.leave.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_leave_id': self.id
            }
        }

    # @api.constrains('request_date_from', 'holiday_status_id', 'is_same_day_confirmed')
    # def _check_same_day_confirmation(self):
    #     for leave in self:
    #         if self.env.context.get('skip_same_day_check'):
    #             continue
    #         if (leave.holiday_status_id.name == '7-Hour Policy Leave' and
    #             leave.request_date_from == fields.Date.today() and
    #             not leave.is_same_day_confirmed):
    #             raise ValidationError("Same-day 7-Hour Policy Leave must be confirmed via the wizard.")

    def _send_creation_notification(self, leave):
        """Send a notification message when the leave is created"""
        # Get the Reporting Manager (Employee's Manager)
        reporting_manager = leave.employee_id.parent_id.user_id
        # Get the CTO from the CTO group
        cto_group = self.env.ref('multi_level_leave_policy.group_cto')
        cto = self.env['res.users'].search([('groups_id', 'in', cto_group.ids)], limit=1)
        # Get HR users from the HR group
        hr_group = self.env.ref('multi_level_leave_policy.group_hr')
        hr_users = self.env['res.users'].search([('groups_id', 'in', hr_group.ids)], limit=1)
        project_manager = leave.employee_id.project_manager_id
        print("=============", project_manager)

        partner_ids = list(filter(None, [
            leave.employee_id.user_id.partner_id.id if leave.employee_id.user_id and leave.employee_id.user_id.partner_id else None,
            reporting_manager.partner_id.id if reporting_manager and reporting_manager.partner_id else None,
            cto.partner_id.id if cto and cto.partner_id else None,
            hr_users.partner_id.id if hr_users and hr_users.partner_id else None,
            project_manager.partner_id.id if project_manager and project_manager else None,
        ]))
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
        today = fields.Date.today()
        cutoff_date = today - timedelta(days=2)

        # Search leaves in 'confirm' state created more than 2 days ago
        pending_leaves = self.search([
            ('state', '=', 'confirm'),
            ('holiday_status_id.name', 'in', ['Casual Leave', 'Sick Leave', 'Emergency Leave']),
            ('create_date', '<=', datetime.combine(cutoff_date, datetime.min.time())),
        ])

        for leave in pending_leaves:
            try:
                leave.action_approve(bypass_user_check=True)
                leave.message_post(
                    body="⏱️ Leave was automatically approved after 2 days without response."
                )
            except Exception as e:
                _logger.error(f"❌ Failed to auto-approve leave {leave.id}: {e}")

    def _get_leave_approval_hierarchy(self, leave):
        """Get the approval hierarchy: Reporting Manager (Employee's Manager) → CTO → HR"""

        # Use the employee's `parent_id` to get the Reporting Manager (Employee's Manager)
        reporting_manager = leave.employee_id.parent_id.user_id

        # Get the CTO user based on the user group (you can replace 'your_module.group_cto' with the actual group)
        cto_group = self.env.ref('multi_level_leave_policy.group_cto')
        cto = self.env['res.users'].search([('groups_id', 'in', cto_group.ids)], limit=1)

        # Get HR user(s) from the HR group
        hr_group = self.env.ref('multi_level_leave_policy.group_hr')
        hr = self.env['res.users'].search([('groups_id', 'in', hr_group.ids)], limit=1)

        return [reporting_manager, cto, hr]

    def action_approve(self, bypass_user_check=False):
        """Override the approve action to enforce the approval hierarchy with special 1-day casual leave handling"""

        # Get group users
        cto_group = self.env.ref('multi_level_leave_policy.group_cto')
        hr_group = self.env.ref('multi_level_leave_policy.group_hr')
        pm_group = self.env.ref('multi_level_leave_policy.group_pm')

        cto_user = self.env['res.users'].search([('groups_id', 'in', cto_group.ids)], limit=1)
        hr_user = self.env['res.users'].search([('groups_id', 'in', hr_group.ids)], limit=1)
        pm_user = self.env['res.users'].search([('groups_id', 'in', pm_group.ids)], limit=1)

        reporting_manager = self.employee_id.parent_id.user_id

        # --- HR can approve any leave at any time ---
        if self.env.user == hr_user or bypass_user_check:
            self.reporting_manager_approved = True
            self.cto_approved = True
            self.hr_approved = True

            self.message_post(
                body=f"Leave fully approved by HR: {self.employee_id.name}",
                partner_ids=[
                    reporting_manager.partner_id.id,
                    cto_user.partner_id.id,
                    pm_user.partner_id.id,
                    hr_user.partner_id.id,
                    self.employee_id.user_id.partner_id.id
                ],
                message_type='notification',
                subtype_xmlid='mail.mt_comment'
            )

            return super(HrLeave, self).action_validate()

        # --- 1-Day Casual Leave auto-approval if approved by Reporting Manager ---
        if self.holiday_status_id.name == 'Casual Leave' and self.number_of_days == 1:
            if self.env.user == reporting_manager:
                self.reporting_manager_approved = True
                self.cto_approved = True
                self.hr_approved = True

                self.message_post(
                    body=f"1-Day Casual Leave approved by Reporting Manager: {self.employee_id.name}.",
                    partner_ids=[
                        cto_user.partner_id.id,
                        pm_user.partner_id.id,
                        hr_user.partner_id.id,
                        self.employee_id.user_id.partner_id.id
                    ],
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )

                return super(HrLeave, self).action_validate()

        if self.holiday_status_id.name == 'Casual Leave' and self.number_of_days >= 2:
            if self.env.user == self.employee_id.project_manager_id:
                self.reporting_manager_approved = True
                self.cto_approved = True
                self.hr_approved = True

                self.message_post(
                    body=f"1-Day Casual Leave approved by Project Manager: {self.employee_id.name}.",
                    partner_ids=[
                        cto_user.partner_id.id,
                        pm_user.partner_id.id,
                        hr_user.partner_id.id,
                        self.employee_id.user_id.partner_id.id
                    ],
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )

                return super(HrLeave, self).action_validate()
        if self.holiday_status_id.name == '7-Hour Policy Leave' and self.number_of_days == 1:
            if self.env.user == reporting_manager:
                self.reporting_manager_approved = True
                self.cto_approved = True
                self.hr_approved = True

                self.message_post(
                    body=f"1-Day Casual Leave approved by Reporting Manager: {self.employee_id.name}.",
                    partner_ids=[
                        cto_user.partner_id.id,
                        pm_user.partner_id.id,
                        hr_user.partner_id.id,
                        self.employee_id.user_id.partner_id.id
                    ],
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )

                return super(HrLeave, self).action_validate()

        # --- Normal Hierarchical Approval Process ---
        if not self.reporting_manager_approved:
            if self.env.user == reporting_manager:
                self.reporting_manager_approved = True
                self.message_post(
                    body=f"Leave approved by Reporting Manager: {self.employee_id.name}",
                    partner_ids=[
                        reporting_manager.partner_id.id,
                        cto_user.partner_id.id,
                        hr_user.partner_id.id,
                        self.employee_id.user_id.partner_id.id
                    ],
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
            else:
                raise ValidationError(_("You are not authorized to approve this leave as Reporting Manager."))

        elif not self.cto_approved:
            if self.env.user == cto_user:
                self.cto_approved = True
                self.message_post(
                    body=f"Leave approved by CTO: {self.employee_id.name}",
                    partner_ids=[
                        reporting_manager.partner_id.id,
                        cto_user.partner_id.id,
                        hr_user.partner_id.id,
                        self.employee_id.user_id.partner_id.id
                    ],
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
            else:
                raise ValidationError(_("You are not authorized to approve this leave as CTO."))

        elif not self.hr_approved:
            raise ValidationError(_("Only HR can approve this leave at the final stage."))

        if self.reporting_manager_approved and self.cto_approved and self.hr_approved:
            return super(HrLeave, self).action_approve()
