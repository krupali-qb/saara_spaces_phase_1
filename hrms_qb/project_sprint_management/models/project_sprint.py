from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class ProjectSprint(models.Model):
    _name = 'project.sprint'
    _description = 'Project Sprint'

    name = fields.Char(string="Sprint Name", required=True)
    description = fields.Text(string="Sprint Description")
    project_id = fields.Many2one('project.project', string="Project", required=True)
    duration = fields.Integer(string="Duration (days)")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    meeting_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly')
    ], string="Meeting Type")
    task_ids = fields.One2many('project.task', 'sprint_id', string="Tasks")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('started', 'Started'),
    ], default='draft', string='Status')
    stage_id = fields.Many2one(
        'project.sprint.stage',
        string='Stage',
        group_expand='_read_group_stage_ids'
    )

    def action_start_sprint(self):
        self.ensure_one()
        for sprint in self:
            if not sprint:
                raise UserError("You cannot start a sprint without tasks.")
            return {
                'type': 'ir.actions.act_window',
                'name': 'Start Sprint',
                'res_model': 'start.sprint.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('project_sprint_management.view_start_sprint_wizard').id,
                'target': 'new',
                'context': {
                    'default_sprint_id': sprint.id,
                    'default_project_id': sprint.project_id.id,
                    'default_name': sprint.name,
                    'default_start_date': sprint.start_date,
                    'default_end_date': sprint.end_date,
                }
            }

    @api.model
    def create(self, vals):
        sprint = super(ProjectSprint, self).create(vals)
        if sprint.state == 'draft':
            stage = self.env['project.sprint.stage'].search([
                ('name', '=', 'Upcoming'),
                ('project_ids', 'in', [sprint.project_id.id])
            ], limit=1)
            sprint.stage_id = stage.id
        return sprint

    def write(self, vals):
        res = super(ProjectSprint, self).write(vals)
        for sprint in self:
            if 'state' in vals:
                if vals['state'] == 'started':
                    stage = self.env['project.sprint.stage'].search([
                        ('name', '=', 'Ongoing'),
                        ('project_ids', 'in', [sprint.project_id.id])
                    ], limit=1)
                    if stage:
                        sprint.stage_id = stage.id
                elif vals['state'] == 'draft':
                    stage = self.env['project.sprint.stage'].search([
                        ('name', '=', 'draft'),
                        ('project_ids', 'in', [sprint.project_id.id])
                    ], limit=1)
                    if stage:
                        sprint.stage_id = stage.id
        return res

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        project_id = None

        for clause in domain:
            if isinstance(clause, (list, tuple)) and clause[0] == 'project_id' and clause[1] in ('=', 'in'):
                project_id = clause[2]
                break

        if not project_id:
            project_id = self.env.context.get('default_project_id')

        if project_id:
            return self.env['project.sprint.stage'].search([('project_ids', 'in', [project_id])], order=order)

        return self.env['project.sprint.stage'].search([], order=order)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def action_view_tasks(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sprints',
            'res_model': 'project.sprint',
            'view_mode': 'kanban,form',  # include form mode!
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }


class ProjectTask(models.Model):
    _inherit = 'project.task'

    project_id = fields.Many2one('project.project', string="Project")
    sprint_id = fields.Many2one('project.sprint', string="Sprint")
    backlog_id = fields.Many2one('project.task', string="Backlog")
    backlog_id_boolean = fields.Boolean(string="Backlog2")
    estimation_pts = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('5', '5'),
        ('8', '8'),
        ('13', '13'),
        ('21', '21')
    ], string="Estimation Points")
    item_type = fields.Selection([
        ('story', 'Story'),
        ('task', 'Task'),
        ('bug', 'Bug')
    ], string="Item Type")

    '''@api.model
    def action_assign_to_sprint(self):
        print("fcffffffffffffffffffffffffffffffffff", self.env.context.get('active_ids'))
        project_task = self.env['project.task'].search([("id", "in", self.env.context.get('active_ids'))])
        print("ccccccccccccccccccccccccc", project_task)
        for task in project_task:
            task.backlog_id_boolean = True
            if task.sprint_id:
                sprint = self.env['project.sprint'].search([("id", "=", task.sprint_id.id)])
                print("ddddddddddddddddddddddddddd", sprint)
                sprint.task_ids.backlog_id = task'''

    @api.model
    def action_assign_to_sprint(self):
        active_ids = self.env.context.get('active_ids')
        return {
            'name': 'Assign Sprint to Tasks',
            'type': 'ir.actions.act_window',
            'res_model': 'assign.sprint.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_task_ids': [(6, 0, active_ids)]},
        }

    points = fields.Integer(string="Points")

    is_active = fields.Boolean(
        string='Is Active',
    )

    task_status = fields.Selection(
        [('active', 'Active'), ('completed', 'Completed')],
        string='Task Status',
        compute='_compute_task_status',
        store=True,
    )

    deadline_status = fields.Selection(
        [('overdue', 'Overdue'), ('upcoming', 'Upcoming'), ('no_deadline', 'No Deadline')],
        string='Deadline Status',
        compute='_compute_deadline_status',
        store=True,
    )

    @api.depends('stage_id.fold')
    def _compute_task_status(self):
        for task in self:
            task.task_status = 'completed' if task.stage_id.fold else 'active' or 'Canceled'

    @api.depends('date_deadline')
    def _compute_deadline_status(self):
        today = date.today()
        for task in self:
            if not task.date_deadline:
                task.deadline_status = 'no_deadline'
            elif task.date_deadline.date() < today:
                task.deadline_status = 'overdue'
            else:
                task.deadline_status = 'upcoming'

    @api.onchange('estimation_pts')
    def _onchange_estimation_pts(self):
        for record in self:
            if record.estimation_pts:
                record.points = int(record.estimation_pts)
            else:
                record.points = 0

    '''def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # Call original method first
        result = super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        # Ensure we are grouping by stage
        if groupby and groupby[0] == 'stage_id':
            # Extract project_id from domain
            project_ids = [term[2] for term in domain if isinstance(term, (list, tuple)) and term[0] == 'project_id' and term[1] == '=']
            if project_ids:
                project_id = project_ids[0]
                stages = self.env['project.task.type'].search([('project_ids', 'in', project_id)])
                print("11111111111111111111111111111111111111",stages)
                existing_stage_ids = [group['stage_id'][0] for group in result if group['stage_id']]
                print("222222222222222222222222222",existing_stage_ids)

                for stage in stages:
                    if stage.id not in existing_stage_ids:
                        group = {
                            '__domain': [('stage_id', '=', stage.id), ('project_id', '=', project_id)],
                            'stage_id': (stage.id, stage.name),
                            '__context': {},
                            '__fold': stage.fold,
                            'project_id': project_id,
                        }
                        print("3333333333333333333333333333",group)
                        # Add dummy 'state' field if expected
                        if 'stage_id' in fields:
                            print("444444444444444444444444444",fields)
                            group['state'] = None  # or 'todo' if you use state
                        result.append(group)
        return result'''

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """
        Show only stages for the selected project in the Kanban view.
        """
        # Get project selected in the search panel or form default
        project_id = None
        for clause in domain:
            if isinstance(clause, (list, tuple)) and clause[0] == 'project_id' and clause[1] == '=':
                project_id = clause[2]
                print("ddddddddddddddddddddddddddddddd", project_id)
                break
        # Only include stages explicitly linked to this project
        stage_domain = [('project_ids', 'in', [project_id])]
        vvv = self.env['project.task.type'].search(stage_domain, order=order)
        print("2222222222222222222222222222", vvv)

        return self.env['project.task.type'].search(stage_domain, order=order)

    stage_id = fields.Many2one(
        'project.task.type',
        string='Stage',
        group_expand='_group_expand_stage_id'
    )

    @api.model
    def _group_expand_stage_id(self, stages, domain, order):
        """
        Show only stages for the selected project in the Kanban view.
        """
        project_id = None

        # Extract project_id from domain
        for clause in domain:
            if isinstance(clause, (list, tuple)) and clause[0] == 'project_id' and clause[1] == '=':
                project_id = clause[2]
                break

        # Fallback to context

        if not project_id:
            # Get from sprint
            sprint_id = self.env.context.get('active_id') or self.env.context.get('default_sprint_id')
            if sprint_id:
                sprint = self.env['project.sprint'].browse(sprint_id)
                project_id = sprint.project_id.id
        print("vvvvvvvvvvvvvvvvvvvv", project_id)
        if not project_id:
            project_id = self.env.context.get('default_project_id')

        # If no project, show all stages (or none)
        if not project_id:
            return self.env['project.task.type'].search([], order=order)

        # Only show stages linked to this project
        return self.env['project.task.type'].search([('project_ids', 'in', [project_id])], order=order)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    sprint_count = fields.Integer(string="Sprint Count", compute='_compute_sprint_count')

    def _compute_sprint_count(self):
        for record in self:
            record.sprint_count = self.env['project.sprint'].search_count([('project_id', '=', record.id)])

    def action_open_start_sprint_wizard(self):
        return {
            'name': 'Start Sprint',
            'type': 'ir.actions.act_window',
            'res_model': 'start.sprint.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_project_id': self.id}
        }
