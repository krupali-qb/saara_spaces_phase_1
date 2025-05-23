from odoo import fields, models, api, exceptions


class VendorPaymentMethod(models.Model):
    _name = "vendor.payment.method"
    _description = 'vendor payments method'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _valid_field_parameter(self, field, name):
        if name == 'tracking':
            return True
        return super()._valid_field_parameter(field, name)

    name = fields.Selection([('cash', 'Cash'), ('bank', 'Bank')], string='Payment Method*', required=True)
    interior_project_id = fields.Many2one('project.interior', string='Interior Project*', compute='_compute_project_id',
                                          store=True)
    vendor_id = fields.Many2one('res.agency', string="Agency*", tracking=True)
    agency_category = fields.Many2one('agency.category', string="Work Category")
    payment_date = fields.Date(string='Payment Date*', tracking=True, required=True)
    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id)
    vendor_payment = fields.Float(string='Payment*', size=25)
    expenses = fields.Boolean(string='Expenses', default=False)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    project_form_id = fields.One2many(comodel_name='vendor.payment.method.line',
                                      inverse_name='agency_id',
                                      copy=True, auto_join=True, required=True)
    total_payment = fields.Float(string="Total Payment", compute="_compute_total_payment", store=True)
    expense_id = fields.Many2one('project.expenses', string='Expenses')
    invoice_number = fields.Char(string='Invoice Number*', size=25)
    
    
    line_limit_reached = fields.Boolean(compute='_compute_line_limit_reached', store=False)
    can_add_linec = fields.Boolean( store=False)

    @api.depends('project_form_id')
    def _compute_line_limit_reached(self):
        for record in self:
            record.line_limit_reached = len(record.line_ids) >= 1
            
            
    line_editable = fields.Boolean(compute='_compute_line_editable', store=False)

    @api.depends('project_form_id')
    def _compute_line_editable(self):
        for rec in self:
            rec.line_editable = len(rec.project_form_id) < 2




    @api.constrains('project_form_id')
    def _check_project_form_id(self):
        for record in self:
            if not record.project_form_id:
                raise exceptions.ValidationError("At least one project form line is required.")

    @api.depends('project_form_id.vendor_payment')
    def _compute_total_payment(self):
        for record in self:
            record.total_payment = sum(record.project_form_id.mapped('vendor_payment'))

    @api.model
    def create(self, vals):
        """Override create method to generate project expense after vendor payment."""
        payment_record = super(VendorPaymentMethod, self).create(vals)
        projects = payment_record.project_form_id
        for project in projects:
            vendor_payment = self.env['vendor.payment.method'].create({
                'name': payment_record.name,
                'vendor_id': payment_record.vendor_id.id,
                'interior_project_id': project.project_id.id,
                'agency_category': project.agency_category.id,
                'payment_date': payment_record.payment_date,
                'vendor_payment': project.vendor_payment,
            })
        if payment_record.interior_project_id:
            print("demo----------", payment_record.interior_project_id)
            if payment_record.expenses == False:
                print("==============if--")
                payment_record.project_form_id = [(0, 0, {
                    'project_id': payment_record.interior_project_id.id,
                    'agency_category': payment_record.agency_category.id,
                    'vendor_payment': payment_record.vendor_payment,
                })]
        return payment_record

    def write(self, vals):
        # Check for attempts to add new lines (command 0) — block if record already has lines
        if 'project_form_id' in vals:
            for cmd in vals['project_form_id']:
                if isinstance(cmd, (list, tuple)) and cmd[0] == 0:
                    for record in self:
                        if record.project_form_id:
                            print("❌ Cannot add more lines to existing record ID", record.id)
                            return True  # silently ignore the addition

        # Extract vendor_payment from update command if present
        updated_vendor_payment = None
        if 'project_form_id' in vals:
            for cmd in vals['project_form_id']:
                if isinstance(cmd, (list, tuple)) and cmd[0] == 1:
                    line_vals = cmd[2] if len(cmd) > 2 else {}
                    if 'vendor_payment' in line_vals:
                        updated_vendor_payment = line_vals['vendor_payment']
                        print("✅ Found vendor_payment in write:", updated_vendor_payment)

        # Proceed with the actual write
        res = super(VendorPaymentMethod, self).write(vals)

        for record in self:
            # Update linked lines only if no expenses and vendor_payment was found
            if not record.expenses and updated_vendor_payment is not None:
                print("=========== Updating lines with vendor_payment:", updated_vendor_payment)
                record.project_form_id.write({
                    'vendor_payment': updated_vendor_payment
                })

            # Update related project.expenses with payment type
            if record.expense_id:
                expense = self.env['project.expenses'].browse(record.expense_id.id)
                if expense.exists():
                    expense.write({
                        'payment_type': record.name
                    })

        return res



class VendorPaymentMethodLine(models.Model):
    _name = "vendor.payment.method.line"

    project_id = fields.Many2one('project.interior', string='Projects*', required=True)
    agency_category = fields.Many2one('agency.category', string="Work Category*")
    vendor_payment = fields.Float(string='Payment*', tracking=True, required=True, size=25)
    agency_id = fields.Many2one('vendor.payment.method', string='Agency')
    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id)
        
        
    def write(self, vals):
        if self.env.context.get('skip_project_update'):
            return super().write(vals)

        res = super().write(vals)
        for record in self:
            projects = self.env['project.interior'].search([('agency_payment_id.id', '=', record.agency_id.id)])
            for project in projects.agency_payment_id:
                if project == record.agency_id:
                    print("ffffffffffffffffffffff",record.vendor_payment,vals)
                    project.with_context(skip_project_update=True).write({
                        'vendor_payment': record.vendor_payment
                    })

            expenses = self.env['project.expenses'].search([
                ('id', '=', record.agency_id.expense_id.id),
            ])
            for expense in expenses:
                expense.with_context(skip_project_update=True).write({
                    'total_amount': record.vendor_payment
                })
                print("expense-----------------",expense)

        return res
        
    
