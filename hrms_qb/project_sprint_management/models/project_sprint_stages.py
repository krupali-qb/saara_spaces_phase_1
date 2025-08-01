from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
class ProjectSprintStage(models.Model):
    _name = 'project.sprint.stage'
    _description = 'Sprint Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True)
    sequence = fields.Integer(default=1)
    project_ids = fields.Many2many('project.project', string='Projects')
    fold = fields.Boolean(string='Folded in Kanban', default=False)
