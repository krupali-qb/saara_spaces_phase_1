from email.policy import default

from odoo import fields, models, api
import re
from odoo.exceptions import ValidationError


class ResAgency(models.Model):
    _name = "res.agency"

    _description = 'Customer Report '
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name*', required=True, size=100)
    street = fields.Char(string='Street*', required=True, size=25)
    street2 = fields.Char(string='Street2', size=25)
    city = fields.Char(string='City*', required=True, size=25)
    state_id = fields.Many2one('res.country.state', string='State*', required=True)
    zip = fields.Char(string='Zip', required=True, size=6)
    country_id = fields.Many2one('res.country', string='Country*', required=True,
                                 default=lambda self: self._default_state())
    phone = fields.Char(string='Phone*', required=True, size=13, default='+91')
    mobile = fields.Char(string='Mobile*', required=True, size=13, default='+91')
    email = fields.Char(string='Email*', required=True, size=50)
    note = fields.Html(string='Note')
    image_1998 = fields.Image(string='Image', store=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    v_project_count = fields.Integer(string="Project Count", compute='compute_vendor_project_count',
                                     default=0)
    tag_id = fields.Selection([('agency', 'Agency'), ('supplier', 'Supplier')], default='agency', tracking=True, string=
    'Tags')
    gst_required = fields.Selection([('applicable', 'Applicable'), ('notapplicable', 'Not Applicable')],
                                    string="GST Applicable", default='notapplicable')
    gst_no = fields.Char(string='GST*', required=False, size=15)
    project_id = fields.Many2one('project.interior', string='Projects')

    @api.onchange('name', 'city', 'street', 'street2', 'note')
    def _onchange_fields(self):
        for field in ['name', 'city', 'street', 'street2', 'note']:
            value = getattr(self, field)
            if value:
                setattr(self, field, value.title())

    @api.model
    def _default_state(self):
        india = self.env.ref('base.in')
        return india.id if india else False

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            self.city = False
            self.zip = False

    @api.constrains('mobile')
    def _check_mobile(self):
        """ Validate mobile number (only digits and length 10) """
        mobile_regex = re.compile(r'^(?:\+91|91)?[6-9]\d{9}$')
        for record in self:
            if record.mobile and not mobile_regex.match(record.mobile):
                raise ValidationError("Invalid Mobile Number! It should contain only digits and be 10 characters long.")

    @api.constrains('phone')
    def _check_phone(self):
        """ Validate mobile number (only digits and length 10) """
        mobile_regex = re.compile(r'^(?:\+91|91)?[6-9]\d{9}$')
        for record in self:
            if record.phone and not mobile_regex.match(record.phone):
                raise ValidationError("Invalid Phone Number! It should contain only digits and be 10 characters long.")

    @api.constrains('email')
    def _check_email(self):
        """ Validate email format """
        email_regex = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
        for record in self:
            if record.email and not email_regex.match(record.email):
                raise ValidationError("Invalid Email Format! Please enter a valid email address.")

    def compute_vendor_project_count(self):
        for record in self:
            record.v_project_count = self.env['project.interior'].search_count(
                [('agency_payment_id.vendor_id', '=', self.id)])

    def action_get_vendor_project_record(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Projects',
            'view_mode': 'tree,form',
            'res_model': 'project.interior',
            'domain': [('agency_payment_id.vendor_id', '=', self.id)],
        }