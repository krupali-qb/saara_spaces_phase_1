from odoo import fields, models, api, exceptions, _


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
        'project.interior', string='Interior Project*', store=True
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

    # 🔁 NEW: Link back to the line (only for re_write=True)
    linked_line_id = fields.Many2one('vendor.payment.method.line', string="Linked Original Line")

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
        payment_record = super(VendorPaymentMethod, self).create(vals)
        projects = payment_record.project_form_id

        for project in projects:
            split_payment = self.env['vendor.payment.method'].create({
                'name': payment_record.name,
                'vendor_id': payment_record.vendor_id.id,
                'interior_project_id': project.project_id.id,
                'agency_category': project.agency_category.id,
                'payment_date': payment_record.payment_date,
                'vendor_payment': project.vendor_payment,
                're_write': True,
                'linked_line_id': project.id,  # NEW: link to the line
            })
            project.cloned_vendor_payment_id = split_payment.id  # NEW: link line to split

        if payment_record.interior_project_id and not payment_record.expenses:
            payment_record.project_form_id = [(0, 0, {
                'project_id': payment_record.interior_project_id.id,
                'agency_category': payment_record.agency_category.id,
                'vendor_payment': payment_record.vendor_payment,
            })]
        elif payment_record.interior_project_id and payment_record.expenses:
            if not payment_record.agency_category:
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
        for record in self:
            if 'project_form_id' in vals:
                commands = vals['project_form_id']
                new_commands = []

                for cmd in commands:
                    if isinstance(cmd, list) and cmd[0] == 0:  # create new line
                        line_data = cmd[2]
                        unique_id = line_data.get('uniqe_id') or self.env['ir.sequence'].next_by_code(
                            'vendor.payment.method.line')
                        if isinstance(line_data, dict):
                            if record.expense_id:
                                new_expense_id = self.env['project.expenses'].create({
                                    'name': record.expense_id.name,
                                    'project_id': line_data.get('project_id'),
                                    'agency_category': line_data.get('agency_category'),
                                    'total_amount': line_data.get('vendor_payment'),
                                    'category_id': record.expense_id.category_id.id,
                                    'expense_date': record.payment_date,
                                    'agency_id': record.vendor_id.id,
                                    'paid_by_employee_id': record.expense_id.paid_by_employee_id.id,
                                    'payment_type': record.expense_id.payment_type,
                                    'uniqe_id': unique_id,
                                })

                                unique_id = self.env['ir.sequence'].next_by_code('vendor.payment.method.line') or _(
                                    'New')
                                new_vpm = self.env['vendor.payment.method'].create({
                                    'name': record.name,
                                    'vendor_id': record.vendor_id.id,
                                    'interior_project_id': line_data.get('project_id'),
                                    'agency_category': line_data.get('agency_category'),
                                    'payment_date': record.payment_date,
                                    'vendor_payment': line_data.get('vendor_payment'),
                                    're_write': True,
                                    'expenses': True,
                                    'expense_id': new_expense_id.id,
                                })
                                line_data['agency_id'] = new_vpm.id
                                line_data['uniqe_id'] = unique_id
                                new_vpm.project_form_id.uniqe_id = line_data['uniqe_id']

                            else:
                                new_vpm = self.env['vendor.payment.method'].create({
                                    'name': record.name,
                                    'vendor_id': record.vendor_id.id,
                                    'interior_project_id': line_data.get('project_id'),
                                    'agency_category': line_data.get('agency_category'),
                                    'payment_date': record.payment_date,
                                    'vendor_payment': line_data.get('vendor_payment'),
                                    're_write': True,
                                })
                                new_vpm.project_form_id.uniqe_id = vals.get("uniqe_id")

                            # 💡 Inject the new vendor_payment_id into the line data
                            line_data['agency_id'] = new_vpm.id
                            new_commands.append([0, 0, line_data])
                        else:
                            new_commands.append(cmd)
                    else:
                        new_commands.append(cmd)
                vals['project_form_id'] = new_commands

        # Continue with update logic (e.g., update project.expenses from line updates)
        for record in self:
            if 'project_form_id' in vals:
                for cmd in vals['project_form_id']:
                    if isinstance(cmd, list) and cmd[0] == 1:
                        line_id = cmd[1]
                        line_vals = cmd[2]
                        if 'vendor_payment' in line_vals:
                            line = self.env['vendor.payment.method.line'].browse(line_id)
                            if line.uniqe_id:
                                uniqe = line.uniqe_id
                                if uniqe and "-" in uniqe and uniqe.upper().startswith("V"):
                                    try:
                                        prefix, number = uniqe.split("-")
                                        uniqe = f"{prefix}-{int(number) - 1:05d}"
                                    except ValueError:
                                        pass
                                    expenses = self.env['project.expenses'].search([
                                        ('project_id', '=', line.project_id.id),
                                        ('agency_category', '=', line.agency_category.id),
                                        ('expense_date', '=', record.payment_date),
                                        ('agency_id', '=', record.vendor_id.id),
                                        ('uniqe_id', '=', uniqe)
                                    ])
                                    expenses.write({'total_amount': line_vals['vendor_payment']})
                                else:
                                    expensesv = self.env['project.expenses'].search([
                                        ('project_id', '=', line.project_id.id),
                                        ('agency_category', '=', line.agency_category.id),
                                        ('expense_date', '=', record.payment_date),
                                        ('agency_id', '=', record.vendor_id.id),
                                        ('id', '=', line.uniqe_id)
                                    ])
                                    expensesv.write({'total_amount': line_vals['vendor_payment']})

        # Sync vendor_payment back if necessary
        for record in self:
            if record.re_write and 'vendor_payment' in vals and record.linked_line_id:
                record.linked_line_id.with_context(skip_project_update=True).write({
                    'vendor_payment': vals['vendor_payment']
                })

        return super(VendorPaymentMethod, self).write(vals)


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
    # vendor_payment_id = fields.Many2one('vendor.payment.method', string="Vendor Payment")
    expense_id = fields.Many2one('project.expenses', string='Expenses')
    exclude_from_total = fields.Boolean(string='Exclude from Total', default=False)

    def _get_default_unique_id(self):
        return self.env['ir.sequence'].next_by_code('vendor.payment.method.line') or _('New')

    uniqe_id = fields.Char(string='Unique ID', readonly=True, copy=False, index=True, )

    # 🔁 Link to cloned vendor.payment.method
    cloned_vendor_payment_id = fields.Many2one('vendor.payment.method', string="Cloned Vendor Payment")

    def write(self, vals):
        if self.env.context.get('skip_project_update'):
            return super().write(vals)

        res = super().write(vals)
        for record in self:
            if 'vendor_payment' in vals and record.cloned_vendor_payment_id:
                record.cloned_vendor_payment_id.with_context(skip_project_update=True).write({
                    'vendor_payment': vals['vendor_payment']
                })

                expenses = self.env['project.expenses'].search([
                    ('id', '=', record.agency_id.expense_id.id),
                ])
                for expense in expenses:
                    expense.with_context(skip_project_update=True).write({
                        'total_amount': vals['vendor_payment']
                    })

        return res

    def unlink(self):
        for record in self:
            if record.cloned_vendor_payment_id:
                record.cloned_vendor_payment_id.unlink()
            related_expenses = self.env['project.expenses'].search([
                ('project_id', '=', record.project_id.id),
                ('agency_category', '=', record.agency_category.id),
                ('total_amount', '=', record.vendor_payment),
                ('agency_id', '=', record.agency_id.vendor_id.id),
                ('expense_date', '=', record.agency_id.payment_date),
            ])
            if related_expenses:
                related_expenses.unlink()
        return super(VendorPaymentMethodLine, self).unlink()
