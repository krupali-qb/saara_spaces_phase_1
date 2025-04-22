# from email.policy import default
from odoo import fields, models, api
import re
from odoo.exceptions import ValidationError


class InteriorProject(models.Model):
    _name = "project.interior"
    _description = 'Customer Report '
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _valid_field_parameter(self, field, name):
        if name == 'tracking':
            return True
        return super()._valid_field_parameter(field, name)

    name = fields.Char(string="Name*", required=True, size=100)
    customer_id = fields.Many2one('res.customer', string="Customer*", required=True)
    cost_price = fields.Float(string="Cost*", tracking=True, size=25)
    agency_payment_id = fields.One2many(comodel_name='vendor.payment.method', domain=[('expenses', '=', False)],
                                        inverse_name='interior_project_id',
                                        string="Vendor Payment",
                                        copy=True, auto_join=True, tracking=True)
    total_expenses_amount = fields.Monetary(string='Total Expenses', store=True,
                                            compute='_compute_total_expenses_amount')
    total_paid = fields.Monetary(string='Total Paid', store=True, compute='_compute_total_paid')
    cost_to_company = fields.Monetary(string='CTC', store=True, compute='_compute_cost_to_company')
    balance_receivable = fields.Monetary(string="Balance Receivable", store=True, compute='_compute_balance_receivable')
    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id)
    payments_ids = fields.One2many(comodel_name='payment.method',
                                   inverse_name='interior_project_id',
                                   string="Customer Payment",
                                   copy=True, auto_join=True)
    agency_amount = fields.Monetary(string='Vendor Amount', store=True, compute='_compute_agency_amounts')
    customer_amount = fields.Monetary(string='Customer Amount', store=True, compute='_compute_customer_amounts')
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    status = fields.Selection(
        [('new', 'New'), ('quote_lock', 'Quote Lock'), ('inprogress', 'In progress'), ('completed', 'Completed')],
        default='new', tracking=True, string=
        'Status')
    street = fields.Char(string='Street*', required=True, size=100)
    street2 = fields.Char(string='Street2', size=100)
    city = fields.Char(string='City*', required=True, size=25)
    state_id = fields.Many2one('res.country.state', string='State*', required=True)
    zip = fields.Char(string='Zip*', required=True, size=6)
    country_id = fields.Many2one('res.country', string='Country*', required=True,
                                 default=lambda self: self._default_state())
    poc_name = fields.Char(string='POC Name*', required=True, size=25)
    contact_information = fields.Char(string='Contact Information*', required=True, size=13, default='+91')
    new_contact_field = fields.Char(string="New Contact", default='+91')
    expenses_ids = fields.One2many(comodel_name='project.expenses',
                                   inverse_name='project_id',
                                   string="Expenses",
                                   copy=True, auto_join=True)
    vendor_id = fields.Many2one('vendor.payment.method', string="Vendor Payment")
    project_form_id = fields.One2many(comodel_name='vendor.payment.method.line',
                                      inverse_name='agency_id',
                                      copy=True, auto_join=True)
    buffer = fields.Integer(string="Buffer (%)")
    quotation_ids = fields.One2many(comodel_name='res.quotation',
                                      inverse_name='interior_project_id',
                                      copy=True, auto_join=True)
    total_amount = fields.Monetary(string="Total Amount:", compute='_compute_qut_total_amount')
    total_ctc = fields.Monetary(string="Total CTC:" ,compute='_compute_total_ctc')
    buffer_avg = fields.Monetary(string="Average:", compute='_compute_buffer_avg')

    @api.onchange('name', 'city', 'street', 'street2', 'poc_name')
    def _onchange_fields(self):
        for field in ['name', 'city', 'street', 'street2', 'poc_name']:
            value = getattr(self, field)
            if value:
                setattr(self, field, value.title())

    @api.onchange('agency_payment_id')
    def _filter_vendor_payments(self):
        if self.agency_payment_id:
            self.agency_payment_id = self.agency_payment_id.filtered(lambda p: not p.expenses)

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            self.city = False
            self.zip = False

    @api.constrains('contact_information')
    def _check_mobile(self):
        """ Validate mobile number (only digits and length 10) """
        mobile_regex = re.compile(r'^(?:\+91|91)?[6-9]\d{9}$')
        for record in self:
            if record.contact_information and not mobile_regex.match(record.contact_information):
                raise ValidationError("Invalid Mobile Number! It should contain only digits and be 10 characters long.")

    @api.model
    def _default_state(self):
        india = self.env.ref('base.in')
        return india.id if india else False

    def action_lock(self):
        self.write({
            'status': 'quote_lock'
        })

    def action_confirm(self):
        self.write({
            'status': 'inprogress'
        })

    def action_done(self):
        self.write({
            'status': 'completed'
        })

    def action_cancel(self):
        self.write({
            'status': 'new'
        })

    @api.depends('cost_price', 'buffer')
    def _compute_cost_to_company(self):
        for record in self:
            record.cost_to_company = record.cost_price * (record.buffer/100)

    @api.depends('quotation_ids.ctc')
    def _compute_total_ctc(self):
        for record in self:
            record.total_ctc = sum(payment.ctc for payment in record.quotation_ids)

    @api.depends('quotation_ids.buffer')
    def _compute_buffer_avg(self):
        for record in self:
            total = 0.0
            count = 0
            for quotation in record.quotation_ids:
                try:
                    buffer_val = float(quotation.buffer or 0.0)
                    total += buffer_val
                    count += 1
                except ValueError:
                    continue
            record.buffer_avg = (total / count) if count > 0 else 0.0


    @api.depends('quotation_ids.amount')
    def _compute_qut_total_amount(self):
        for record in self:
            record.total_amount = sum(payment.amount for payment in record.quotation_ids)


    @api.depends('agency_amount', 'total_expenses_amount')
    def _compute_total_paid(self):
        for record in self:
            record.total_paid = record.agency_amount + record.total_expenses_amount

    @api.depends('cost_price', 'customer_amount')
    def _compute_balance_receivable(self):
        for record in self:
            record.balance_receivable = record.cost_price - record.customer_amount

    @api.depends('payments_ids.customer_payment')
    def _compute_customer_amounts(self):
        for record in self:
            record.customer_amount = sum(payment.customer_payment for payment in record.payments_ids)

    @api.depends('agency_payment_id.vendor_payment')
    def _compute_agency_amounts(self):
        for record in self:
            record.agency_amount = sum(payment.vendor_payment for payment in record.agency_payment_id)

    @api.depends('expenses_ids.total_amount')
    def _compute_total_expenses_amount(self):
        for record in self:
            record.total_expenses_amount = sum(expenses.total_amount for expenses in record.expenses_ids)

