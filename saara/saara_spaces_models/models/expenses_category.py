from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    jwt_token = fields.Char(string='JWT Token')

class ProjectExpenses(models.Model):
    _name = "expenses.category"
    _description = 'Project Expenses category'

    name = fields.Char(string="Name", required=True, size=50)


    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.name = self.name.title()


class AgencyCategory(models.Model):
    _name = "agency.category"
    _description = 'Project agency category'

    name = fields.Char(string="Name", required=True, size=100)

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.name = self.name.title()




   
