from odoo import fields, models, api


class ResReports(models.Model):
    _name = "res.reports"
    _description = 'Reports'

    name = fields.Char(string='Name')