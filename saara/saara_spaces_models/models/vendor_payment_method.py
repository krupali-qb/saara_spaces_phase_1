from odoo import fields, models, api, exceptions


class VendorPaymentMethod(models.Model):
    _name = "vendor.payment.method"
    _description = 'Vendor Payment Method'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _valid_field_parameter(self, field, name):
        if name == 'tracking':
            return True
        return super()._valid_field_parameter(field, name)

    name = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank')
    ], string='Payment Method*', required=True)

    interior_project_id = fields.Many2one(
        'project.interior', string='Interior Project*',
        store=True
    )
    vendor_id = fields.Many2one('res.agency', string="Agency*", tracking=True)
    agency_category = fields.Many2one('agency.category', string="Work Category")
    payment_date = fields.Date(string='Payment Date*', tracking=True, required=True)
    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    vendor_payment = fields.Float(string='Payment*', size=25)
    expenses = fields.Boolean(string='Expenses', default=False)
    company_id = fields.Many2one(
        'res.company', string='Company', index=True,
        default=lambda self: self.env.company
    )
    project_form_id = fields.One2many(
        comodel_name='vendor.payment.method.line',
        inverse_name='agency_id', copy=True, auto_join=True, required=True
    )
    total_payment = fields.Float(string="Total Payment", compute="_compute_total_payment", store=True)
    expense_id = fields.Many2one('project.expenses', string='Expenses')
    invoice_number = fields.Char(string='Invoice Number*', size=25)
    re_write = fields.Boolean(default=False)
    exclude_from_total = fields.Boolean(string='Exclude from Total', default=False)

    @api.constrains('project_form_id')
    def _check_project_form_id(self):
        for record in self:
            if not record.project_form_id:
                raise exceptions.ValidationError("At least one project form line is required.")

    @api.depends('project_form_id.vendor_payment')
    def _compute_total_payment(self):
        for record in self:
            # if len(record.project_form_id) > 1:
            #     continue
            record.total_payment = sum(record.project_form_id.mapped('vendor_payment'))

    @api.model
    def create(self, vals):
        payment_record = super(VendorPaymentMethod, self).create(vals)
        projects = payment_record.project_form_id

        for project in projects:
            self.env['vendor.payment.method'].create({
                'name': payment_record.name,
                'vendor_id': payment_record.vendor_id.id,
                'interior_project_id': project.project_id.id,
                'agency_category': project.agency_category.id,
                'payment_date': payment_record.payment_date,
                'vendor_payment': project.vendor_payment,
                're_write': True,
            })

        if payment_record.interior_project_id and not payment_record.expenses:
            print("============if")
            payment_record.project_form_id = [(0, 0, {
                'project_id': payment_record.interior_project_id.id,
                'agency_category': payment_record.agency_category.id,
                'vendor_payment': payment_record.vendor_payment,
            })]
        elif payment_record.interior_project_id and payment_record.expenses:
            if not payment_record.agency_category:
                print("payment_record.agency_category== False")
                payment_record.project_form_id = [(0, 0, {
                    'project_id': payment_record.expense_id.project_id.id,
                    'agency_category': payment_record.expense_id.agency_category.id,
                    'vendor_payment': payment_record.expense_id.total_amount,
                })]
            else:
                payment_record.project_form_id = [(0, 0, {
                    'project_id': payment_record.interior_project_id.id,
                    'agency_category': payment_record.agency_category.id,
                    'vendor_payment': payment_record.vendor_payment,
                })]
        return payment_record

    def write(self, vals):
        for recoed in self:
            print("=======self.expense_id", recoed.expense_id)
            if recoed.expense_id:
                if vals.get('project_form_id'):
                    commands = vals['project_form_id']
                    for cmd in commands:
                        if isinstance(cmd, list) and cmd[0] == 0:
                            line_data = cmd[2]
                            if isinstance(line_data, dict):
                                new_vpm =  self.env['vendor.payment.method'].create({
                                    'name': self.name,
                                    'vendor_id': self.vendor_id.id,
                                    'interior_project_id': line_data.get('project_id'),
                                    'agency_category': line_data.get('agency_category'),
                                    'payment_date': self.payment_date,
                                    'vendor_payment': line_data.get('vendor_payment'),
                                    're_write': True,
                                    'expenses': True
                                })
                                print("=============new_vpm=",new_vpm)
                                self.env['project.expenses'].create({
                                    'name': self.expense_id.name,
                                    'project_id': line_data.get('project_id'),
                                    'agency_category': line_data.get('agency_category'),
                                    'total_amount': line_data.get('vendor_payment'),
                                    'category_id': self.expense_id.category_id.id,
                                    'expense_date': self.payment_date,
                                    'agency_id': self.vendor_id.id,
                                    'paid_by_employee_id': self.expense_id.paid_by_employee_id.id,
                                    'payment_type': self.expense_id.payment_type,
                                    # 'vendor_payment_id': new_vpm.id
                                })

            else:
                if vals.get('project_form_id'):
                    commands = vals['project_form_id']
                    for cmd in commands:
                        if isinstance(cmd, list) and cmd[0] == 0:
                            line_data = cmd[2]
                            if isinstance(line_data, dict):
                                self.env['vendor.payment.method'].create({
                                    'name': self.name,
                                    'vendor_id': self.vendor_id.id,
                                    'interior_project_id': line_data.get('project_id'),
                                    'agency_category': line_data.get('agency_category'),
                                    'payment_date': self.payment_date,
                                    'vendor_payment': line_data.get('vendor_payment'),
                                    're_write': True,
                                })
        res = super(VendorPaymentMethod, self).write(vals)
        return res


class VendorPaymentMethodLine(models.Model):
    _name = "vendor.payment.method.line"

    project_id = fields.Many2one('project.interior', string='Projects*', required=True)
    agency_category = fields.Many2one('agency.category', string="Work Category*")
    vendor_payment = fields.Float(string='Payment*', tracking=True, required=True, size=25)
    agency_id = fields.Many2one('vendor.payment.method', string='Agency')
    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id
    )
    exclude_from_total = fields.Boolean(string='Exclude from Total', default=False)

    def write(self, vals):
        if self.env.context.get('skip_project_update'):
            return super().write(vals)

        res = super().write(vals)
        for record in self:
            projects = self.env['project.interior'].search([
                ('agency_payment_id.id', '=', record.agency_id.id)
            ])
            for project in projects.agency_payment_id:
                if project == record.agency_id:
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

        return res

    def unlink(self):
        for record in self:
            # Find related vendor.payment.method records with re_write=True
            related_vendor_payments = self.env['vendor.payment.method'].search([
                ('re_write', '=', True),
                ('interior_project_id', '=', record.project_id.id),
                ('agency_category', '=', record.agency_category.id),
                ('vendor_payment', '=', record.vendor_payment),
                ('vendor_id', '=', record.agency_id.vendor_id.id),
                ('payment_date', '=', record.agency_id.payment_date),
            ])
            if related_vendor_payments:
                print("======related_vendor_payments========", related_vendor_payments)
                related_vendor_payments.unlink()
        return super(VendorPaymentMethodLine, self).unlink()
