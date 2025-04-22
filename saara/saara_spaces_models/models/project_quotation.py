from odoo import fields, models, api


class ProjectQuotation(models.Model):
    _name = "res.quotation"

    _description = 'Quotation For Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    interior_project_id = fields.Many2one('project.interior', string='Interior Project*', compute='_compute_project_id',
                                          store=True)
    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    agency_category = fields.Many2one('agency.category', string="Work Category")
    buffer = fields.Char(string="Buffer%", compute="_compute_buffer", inverse="_inverse_buffer", store=True)
    ctc = fields.Float(string="CTC", compute="_compute_ctc_payment")
    amount = fields.Float(string="Total Amount*")
    vendor_id = fields.Many2one('res.agency', string="Agency*", tracking=True)



    def _inverse_buffer(self):
        for record in self:
            if record.interior_project_id:
                record.buffer = record.buffer

    @api.depends('interior_project_id')
    def _compute_buffer(self):
        for record in self:
            record.buffer = record.interior_project_id.buffer if record.interior_project_id else ''

    @api.depends('interior_project_id', 'buffer')
    def _compute_ctc_payment(self):
        for record in self:
            # Example logic (you can adjust this as per your real computation)
            if record.interior_project_id:
                base_ctc = float(record.interior_project_id.cost_to_company or 0.0)
                buffer_percent = float(record.buffer or 0.0)
                record.ctc = str(base_ctc + (base_ctc * buffer_percent / 100))
            else:
                record.ctc = ''
