# from email.policy import default
from odoo import fields, models, api, _
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
    cost_price = fields.Float(string="Cost*", tracking=True, size=50)
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
    street = fields.Char(string='Street*', required=True, size=1000)
    street2 = fields.Char(string='Street2', size=1000)
    city = fields.Char(string='City*', required=True, size=50)
    state_id = fields.Many2one('res.country.state', string='State*', required=True)
    zip = fields.Char(string='Zip*', required=True, size=6)
    country_id = fields.Many2one('res.country', string='Country*', required=True,
                                 default=lambda self: self._default_state())
    poc_name = fields.Char(string='POC Name*', required=True, size=50)
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
                                    copy=True, auto_join=True, tracking=True)
    q_total_amount_paid= fields.Monetary(string='Q Total Amount', compute='_q_total_paid_amount')

    total_amount = fields.Monetary(string="Total Amount:", compute='_compute_qut_total_amount')
    total_ctc = fields.Monetary(string="Total CTC:", compute='_compute_total_ctc')
    buffer_avg = fields.Char(string="Average:", compute='_compute_buffer_avg', store=True)
    pending_ctc = fields.Monetary(string='Pending CTC', compute='_compute_pending_ctc')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The name must be unique!')
    ]

    # @api.constrains('cost_price', 'total_amount')
    # def _check_cost_equals_total(self):
    #     for record in self:
    #         print("---------------if",record)
    #         if record.cost_price != record.total_amount:
    #             print("================================",record.cost_price)
    #             raise ValidationError("Cost Price and Total Amount must be the same.")

    def write(self, vals):
        # Track specific fields inside quotation_ids
        tracked_fields = ['agency_category', 'amount']  # Add more fields as needed

        for record in self:
            # Store the original values of quotation fields before the write
            old_quotation_values = {
                q.id: {f: q[f] for f in tracked_fields}
                for q in record.quotation_ids
            }

        # --- PART 1: Vendor Payment Propagation ---
        if 'agency_payment_id' in vals:
            for cmd in vals['agency_payment_id']:
                if isinstance(cmd, (list, tuple)) and cmd[0] == 1:  # Update command
                    vendor_method_id = cmd[1]
                    line_vals = cmd[2] if len(cmd) > 2 else {}
                    if 'vendor_payment' in line_vals:
                        updated_vendor_payment = line_vals['vendor_payment']
                        vendor_method = self.env['vendor.payment.method'].browse(vendor_method_id)
                        for line in vendor_method.project_form_id:
                            line.write({'vendor_payment': updated_vendor_payment})

        # Perform the actual write
        res = super().write(vals)

        # --- PART 2: Log Quotation Line Field Changes ---
        for record in self:
            new_quotation_values = {
                q.id: {f: q[f] for f in tracked_fields}
                for q in record.quotation_ids
            }

            messages = []
            for qid, new_vals in new_quotation_values.items():
                if qid in old_quotation_values:
                    old_vals = old_quotation_values[qid]
                    for field in tracked_fields:
                        old_val = old_vals[field]
                        new_val = new_vals[field]
                        if old_val != new_val:
                            quotation = self.env['res.quotation'].browse(qid)

                            # Clean display for Many2one fields and None values
                            def get_display(val):
                                if not val:
                                    return "N/A"
                                elif hasattr(val, 'name'):
                                    return val.name
                                else:
                                    return str(val)

                            old_display = get_display(old_val)
                            new_display = get_display(new_val)

                            messages.append(
                                _("%s -> %s") % (
                                    old_display,
                                    new_display
                                )
                            )

            if messages:
                record.message_post(body="<br/>".join(messages))

        return res

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
    def _compute_pending_ctc(self):
        for record in self:
            if record.total_ctc == 0.0:
                record.pending_ctc = 0.0
            else:
                record.pending_ctc = record.total_ctc - record.total_paid

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
            record.buffer_avg = f"{(total / count):.2f}%" if count > 0 else "0.00%"

    @api.depends('quotation_ids.amount')
    def _compute_qut_total_amount(self):
        for record in self:
            record.total_amount = sum(payment.amount for payment in record.quotation_ids)

    @api.depends('quotation_ids.q_total_paid')
    def _q_total_paid_amount(self):
        for record in self:
            record.q_total_amount_paid = sum(paid.q_total_paid for paid in record.quotation_ids)

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
