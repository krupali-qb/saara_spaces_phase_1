from odoo import fields, models, api


class PaymentMethod(models.Model):
    _name = "payment.method"
    _description = 'Payments Methods Customer'

    name = fields.Selection([('cash', 'Cash'),('bank','Bank')],string='Payment Method*', required=True)
    interior_project_id = fields.Many2one('project.interior', string='Interior Project*')
    form_customer_id = fields.Many2one('res.customer', string="Customer",  compute='_compute_partner', required=True)
    customer_id = fields.Many2one('res.customer', string="Customer",  compute='_compute_payment_partner', required=True)
    payment_date = fields.Date(string='Payment Date*',required=True)
    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id)
    customer_payment = fields.Float(string='Payment*',required=True, size=25)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    sale_invoice = fields.Char(string="Sales Invoice*", size=25)


    @api.depends('name')
    def _compute_payment_partner(self):
        for res in self:
            res.customer_id = res.interior_project_id.customer_id

    @api.depends('interior_project_id')
    def _compute_partner(self):
        for res in self:
            res.form_customer_id = res.interior_project_id.customer_id











