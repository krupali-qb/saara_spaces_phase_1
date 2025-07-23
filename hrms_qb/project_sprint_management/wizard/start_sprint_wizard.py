from odoo import models, fields,api
from datetime import timedelta, datetime
from odoo.fields import Date, Datetime
from odoo.exceptions import UserError


class StartSprintWizard(models.TransientModel):
    _name = 'start.sprint.wizard'
    _description = 'Start Sprint Wizard'

    project_id = fields.Many2one('project.project', string="Project", required=True)
    name = fields.Char(string="Sprint Name", required=True)
    sprint_id = fields.Many2one('project.sprint', string='Sprint')
    start_date = fields.Datetime(string="Start Date", required=True)
    end_date = fields.Datetime(string="End Date", required=True)
    meeting = fields.Boolean(string="Schedule Meeting?")
    meeting_time = fields.Float(string="Meeting Time")
    duration = fields.Float(string="Duration (Hours)", default=1.0)
    meeting_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly')
    ], string="Meeting Type")
    reminder_id = fields.Many2one('calendar.alarm', string='Remainder')

    def action_start_meetings(self):
        if self.meeting:
            meetings = []
            date = self.start_date
            end = self.end_date

            while date <= end:
                if self.meeting_type == 'daily':
                    # Skip weekends
                    if date.weekday() < 5:
                        meeting_datetime = datetime.combine(date, datetime.min.time()) + timedelta(
                            hours=self.meeting_time)
                        meeting_stop = meeting_datetime + timedelta(hours=self.duration)

                        meetings.append({
                            'name': self.name,
                            'start': meeting_datetime,
                            'stop': meeting_stop,
                            'allday': False,
                            'alarm_ids': [(4, self.reminder_id.id)] if self.reminder_id else False,
                            'partner_ids': [(6, 0, self.project_id.message_partner_ids.ids)],
                        })
                    date += timedelta(days=1)

                elif self.meeting_type == 'weekly':
                    # Ensure we only create one recurring weekly event on a weekday
                    if date.weekday() < 5:
                        meeting_datetime = datetime.combine(date, datetime.min.time()) + timedelta(
                            hours=self.meeting_time)
                        meeting_stop = meeting_datetime + timedelta(hours=self.duration)

                        meetings.append({
                            'name': self.name,
                            'start': meeting_datetime,
                            'stop': meeting_stop,
                            'allday': False,
                            'alarm_ids': [(4, self.reminder_id.id)] if self.reminder_id else False,
                            'partner_ids': [(6, 0, self.project_id.message_partner_ids.ids)],
                            'recurrency': True,
                            'rrule_type': 'weekly',
                            'tue': True,
                            'interval': 2,
                            'end_type': 'end_date',
                            'until': datetime(2025, 9, 30),
                        })
                        break  # Only create one recurring event
                    else:
                        date += timedelta(days=1)

            self.env['calendar.event'].create(meetings)
            self.sprint_id.state = 'started'
        else:
            self.sprint_id.state = 'started'

        return {'type': 'ir.actions.act_window_close'}

class AssignSprintWizard(models.TransientModel):
    _name = 'assign.sprint.wizard'
    _description = 'Assign Sprint Wizard'

    sprint_id = fields.Many2one('project.sprint', string='Sprint', required=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['task_ids'] = self.env.context.get('active_ids', [])
        return res

    task_ids = fields.Many2many('project.task', string='Tasks')

    def action_assign(self):
        for task in self.task_ids:
            task.sprint_id = self.sprint_id
