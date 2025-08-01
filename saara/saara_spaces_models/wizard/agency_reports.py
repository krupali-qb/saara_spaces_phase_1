from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date
from collections import defaultdict
import io
import xlsxwriter
import base64
from datetime import datetime


class AgencyWizard(models.TransientModel):
    _name = 'agency.report'
    _description = 'Agency Wizard'

    def _default_start_date(self):
        """Returns the first day of the current month."""
        today = date.today()
        return today.replace(day=1)

    def _default_end_date(self):
        """Returns today's date."""
        return date.today()

    start_date = fields.Date(string='Start Date', required=True, default=_default_start_date)
    end_date = fields.Date(string='End Date', required=True, default=_default_end_date)
    agency_ids = fields.Many2many('res.agency', string="Agency")

    @api.model
    def default_get(self, fields):
        res = super(AgencyWizard, self).default_get(fields)
        return res

    def agency_generate_report(self):
        if self.start_date > self.end_date:
            raise UserError('Start date cannot be later than end date.')

        company_logo = self.env.company.logo
        currency_id = self.env.company.currency_id.symbol
        report_data_list = []

        if self.agency_ids:
            for agency in self.agency_ids:
                generated_data = self._generate_data(self.start_date, self.end_date, agency)
                grouped_by_project = self._group_by_project(generated_data['report_data'])

                agency_data = {
                    'agency_ids': agency.name,
                    'currency_id': currency_id,
                    'project_groups': grouped_by_project,  # <-- grouped result here
                    'TOTAL_paid': generated_data['total_expense_sum'] + generated_data['total_vendor_sum'],
                    'total_cash_payment': generated_data['total_cash_payment'],
                    'total_bank_payment': generated_data['total_bank_payment'],
                    'TOTAL_CTC': generated_data['TOTAL_CTC'],
                    'TOTAL_remaining': generated_data['TOTAL_CTC'] - (
                            generated_data['total_expense_sum'] + generated_data['total_vendor_sum'])
                }
                report_data_list.append(agency_data)
            report_data = {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'company_logo': company_logo,
                'currency_id': currency_id,
                'data': report_data_list,
            }
            return self.env.ref('saara_spaces_models.agency_report_action_template_new').report_action(self,
                                                                                                       data=report_data)
        else:
            report_data_list = []
            all_agencies = self.env['res.agency'].search([])

            for agency in all_agencies:
                generated_data = self._generate_data(self.start_date, self.end_date, agency)
                grouped_by_project = self._group_by_project(generated_data['report_data'])

                agency_data = {
                    'agency_ids': agency.name,
                    'currency_id': currency_id,
                    'project_groups': grouped_by_project,
                    'TOTAL_paid': generated_data['total_expense_sum'] + generated_data['total_vendor_sum'],
                    'total_cash_payment': generated_data['total_cash_payment'],
                    'total_bank_payment': generated_data['total_bank_payment'],
                    'TOTAL_CTC': generated_data['TOTAL_CTC'],
                    'TOTAL_remaining': generated_data['TOTAL_CTC'] - (
                            generated_data['total_expense_sum'] + generated_data['total_vendor_sum']
                    ),
                }
                report_data_list.append(agency_data)

            report_data = {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'company_logo': company_logo,
                'currency_id': currency_id,
                'data': report_data_list,
            }

            return self.env.ref('saara_spaces_models.agency_report_action_template_new').report_action(self,
                                                                                                       data=report_data)

    def _generate_data(self, start_date, end_date, agency_id):
        # Fetch the records from the project.interior model
        today = date.today()
        if agency_id:
            projects = self.env['project.expenses'].search([
                ('expense_date', '>=', start_date),
                ('expense_date', '<=', end_date),
                ('agency_id', '=', agency_id.id),
            ])
            quotation_ids = self.env['res.quotation'].search([
                ('create_date', '>=', start_date),
                ('create_date', '<=', end_date),
                ('vendor_id', '=', agency_id.id),
            ])
            vendor_projects = self.env['vendor.payment.method'].search([
                ('payment_date', '>=', start_date),
                ('payment_date', '<=', end_date),
                ('vendor_id', '=', agency_id.id),
                ('expenses', '=', False),
                ('interior_project_id', '!=', False)
            ])
            report_data_new = []
            total_expense_sum = 0  # Initialize the sum for total_amount_expense
            total_vendor_sum = 0
            total_cash_payment = 0  # Initialize the sum for cash payments
            total_bank_payment = 0
            TOTAL_CTC = 0
            for expense in projects:
                project_data = {
                    'expenses_ids': [],
                }
                total_expense_sum += expense.total_amount
                if expense.payment_type == 'cash':
                    total_cash_payment += expense.total_amount  # Sum cash payments for expense
                elif expense.payment_type == 'bank':
                    total_bank_payment += expense.total_amount
                project_data['expenses_ids'].append({
                    'agency_id': expense.agency_id.name,
                    'project_id': expense.project_id.name,
                    'agency_category': expense.agency_category.name,
                    'payment_type': expense.payment_type,
                    'expense_date': expense.expense_date,
                    'type': 'Expense',
                    'total_cost': expense.project_id.cost_price,
                    'customer_amount': expense.project_id.customer_amount,
                    'pending': expense.project_id.balance_receivable,
                    'total_amount': expense.project_id.total_paid,
                    'total_amount_expense': expense.total_amount,
                    'currency_id': expense.currency_id.symbol,
                    'remark': expense.remark,

                })
                report_data_new.append(project_data)
            for vendor in vendor_projects:
                for payment_line in vendor.project_form_id:
                    project_datav = {
                        'vendor_ids': [],
                    }
                    total_vendor_sum += payment_line.vendor_payment
                    if vendor.name == 'cash':
                        total_cash_payment += payment_line.vendor_payment  # Sum cash payments for vendor
                    elif vendor.name == 'bank':
                        total_bank_payment += payment_line.vendor_payment
                    project_datav['vendor_ids'].append({
                        'agency_id': vendor.vendor_id.name,
                        'type': 'Debit',
                        'agency_category': payment_line.agency_category.name,
                        'payment_type': vendor.name,
                        'payment_date': vendor.payment_date,
                        'currency_id': vendor.currency_id.symbol,
                        'project_id': payment_line.project_id.name,
                        'total_cost': payment_line.project_id.cost_price,
                        'paid_amount': payment_line.project_id.total_paid,
                        'pending': payment_line.project_id.balance_receivable,
                        'total_amount_vendor': payment_line.vendor_payment,
                        'invoice_number': vendor.invoice_number

                    })
                    report_data_new.append(project_datav)
            for quotation in quotation_ids:
                TOTAL_CTC += quotation.ctc
            return {
                'report_data': report_data_new,
                'total_expense_sum': total_expense_sum,
                'total_vendor_sum': total_vendor_sum,
                'total_cash_payment': total_cash_payment,
                'total_bank_payment': total_bank_payment,
                'TOTAL_CTC': TOTAL_CTC
            }

        if not agency_id:
            report_data_all = []
            agency_ids = self.env['res.agency'].search([])
            projects_all = self.env['project.expenses'].search([
                ('expense_date', '>=', start_date),
                ('expense_date', '<=', end_date),
            ])
            quotation_ids = self.env['res.quotation'].search([
                ('create_date', '>=', start_date),
                ('create_date', '<=', end_date),
            ])
            vendor_projects_all = self.env['vendor.payment.method'].search([
                ('payment_date', '>=', start_date),
                ('payment_date', '<=', end_date),
                ('expenses', '=', False),
                ('interior_project_id', '!=', False)
            ])

            for agency in agency_ids:
                project_data = {
                    'agency_ids': agency.name,
                    'expenses_ids': [],
                    'vendor_ids': [],
                    'total_paid': 0,
                    'total_vendor': 0,
                    'TOTAL_CTC': 0,
                }
                for quotation in quotation_ids:
                    if quotation.vendor_id == agency:
                        quotation_total_ctc = quotation.ctc
                        project_data['TOTAL_CTC'] += quotation_total_ctc

                for expense in projects_all:
                    if expense.agency_id == agency:
                        expense_amount = expense.total_amount
                        project_data['expenses_ids'].append({
                            'agency_id': expense.agency_id.name,
                            'project_id': expense.project_id.name,
                            'agency_category': expense.agency_category.name,
                            'payment_type': expense.payment_type,
                            'expense_date': expense.expense_date,
                            'type': 'Expense',
                            'total_cost': expense.project_id.cost_price,
                            'customer_amount': expense.project_id.customer_amount,
                            'pending': expense.project_id.balance_receivable,
                            'total_amount': expense.project_id.total_paid,
                            'total_amount_expense': expense.total_amount,
                            'currency_id': expense.currency_id.symbol,
                            'remark': expense.remark
                        })
                        project_data['total_paid'] += expense_amount

                for vendor in vendor_projects_all:
                    for payment_line in vendor.project_form_id:
                        if vendor.vendor_id == agency:
                            vendor_amount = payment_line.vendor_payment
                            project_data['vendor_ids'].append({
                                'agency_id': vendor.vendor_id.name,
                                'type': 'Debit',
                                'agency_category': payment_line.agency_category.name,
                                'payment_type': vendor.name,
                                'payment_date': vendor.payment_date,
                                'project_id': payment_line.project_id.name,
                                'total_cost': payment_line.project_id.cost_price,
                                'paid_amount': payment_line.project_id.total_paid,
                                'pending': payment_line.project_id.balance_receivable,
                                'total_amount_vendor': payment_line.vendor_payment,
                                'currency_id': payment_line.currency_id.symbol,
                                'invoice_number': vendor.invoice_number
                            })
                            project_data['total_vendor'] += vendor_amount
                # Append project data to the report list only if it contains expenses or vendor data
                if project_data['expenses_ids'] or project_data['vendor_ids']:
                    report_data_all.append(project_data)

            return {
                'report_data': report_data_all,
            }
        return None

    def _generate_data_mobile(self, start_date, end_date, agency):
        # Fetch the records from the project.interior model
        today = date.today()
        if agency:
            agency_id = self.env['res.agency'].sudo().search([('id','=',agency)])
            if agency_id:
                projects = self.env['project.expenses'].search([
                    ('expense_date', '>=', start_date),
                    ('expense_date', '<=', end_date),
                    ('agency_id', '=', agency_id.id),
                ])
                quotation_ids = self.env['res.quotation'].search([
                    ('create_date', '>=', start_date),
                    ('create_date', '<=', end_date),
                    ('vendor_id', '=', agency_id.id),
                ])
                vendor_projects = self.env['vendor.payment.method'].search([
                    ('payment_date', '>=', start_date),
                    ('payment_date', '<=', end_date),
                    ('vendor_id', '=', agency_id.id),
                    ('expenses', '=', False),
                    ('interior_project_id', '!=', False)
                ])
                report_data_new = []
                total_expense_sum = 0  # Initialize the sum for total_amount_expense
                total_vendor_sum = 0
                total_cash_payment = 0  # Initialize the sum for cash payments
                total_bank_payment = 0
                TOTAL_CTC = 0
                for expense in projects:
                    project_data = {
                        'expenses_ids': [],
                    }
                    total_expense_sum += expense.total_amount
                    if expense.payment_type == 'cash':
                        total_cash_payment += expense.total_amount  # Sum cash payments for expense
                    elif expense.payment_type == 'bank':
                        total_bank_payment += expense.total_amount
                    project_data['expenses_ids'].append({
                        'agency_id': expense.agency_id.name,
                        'project_id': expense.project_id.name,
                        'agency_category': expense.agency_category.name,
                        'payment_type': expense.payment_type,
                        'expense_date': expense.expense_date,
                        'type': 'Expense',
                        'total_cost': expense.project_id.cost_price,
                        'customer_amount': expense.project_id.customer_amount,
                        'pending': expense.project_id.balance_receivable,
                        'total_amount': expense.project_id.total_paid,
                        'total_amount_expense': expense.total_amount,
                        'currency_id': expense.currency_id.symbol,
                        'remark': expense.remark,

                    })
                    report_data_new.append(project_data)
                for vendor in vendor_projects:
                    for payment_line in vendor.project_form_id:
                        project_datav = {
                            'vendor_ids': [],
                        }
                        total_vendor_sum += payment_line.vendor_payment
                        if vendor.name == 'cash':
                            total_cash_payment += payment_line.vendor_payment  # Sum cash payments for vendor
                        elif vendor.name == 'bank':
                            total_bank_payment += payment_line.vendor_payment
                        project_datav['vendor_ids'].append({
                            'agency_id': vendor.vendor_id.name,
                            'type': 'Debit',
                            'agency_category': payment_line.agency_category.name,
                            'payment_type': vendor.name,
                            'payment_date': vendor.payment_date,
                            'currency_id': vendor.currency_id.symbol,
                            'project_id': payment_line.project_id.name,
                            'total_cost': payment_line.project_id.cost_price,
                            'paid_amount': payment_line.project_id.total_paid,
                            'pending': payment_line.project_id.balance_receivable,
                            'total_amount_vendor': payment_line.vendor_payment,
                            'invoice_number': vendor.invoice_number

                        })
                        report_data_new.append(project_datav)
                for quotation in quotation_ids:
                    TOTAL_CTC += quotation.ctc
                return {
                    'report_data': report_data_new,
                    'total_expense_sum': total_expense_sum,
                    'total_vendor_sum': total_vendor_sum,
                    'total_cash_payment': total_cash_payment,
                    'total_bank_payment': total_bank_payment,
                    'TOTAL_CTC': TOTAL_CTC
                }

            if not agency_id:
                report_data_all = []
                agency_ids = self.env['res.agency'].search([])
                projects_all = self.env['project.expenses'].search([
                    ('expense_date', '>=', start_date),
                    ('expense_date', '<=', end_date),
                ])
                quotation_ids = self.env['res.quotation'].search([
                    ('create_date', '>=', start_date),
                    ('create_date', '<=', end_date),
                ])
                vendor_projects_all = self.env['vendor.payment.method'].search([
                    ('payment_date', '>=', start_date),
                    ('payment_date', '<=', end_date),
                    ('expenses', '=', False),
                    ('interior_project_id', '!=', False)
                ])

                for agency in agency_ids:
                    project_data = {
                        'agency_ids': agency.name,
                        'expenses_ids': [],
                        'vendor_ids': [],
                        'total_paid': 0,
                        'total_vendor': 0,
                        'TOTAL_CTC': 0,
                    }
                    for quotation in quotation_ids:
                        if quotation.vendor_id == agency:
                            quotation_total_ctc = quotation.ctc
                            project_data['TOTAL_CTC'] += quotation_total_ctc

                    for expense in projects_all:
                        if expense.agency_id == agency:
                            expense_amount = expense.total_amount
                            project_data['expenses_ids'].append({
                                'agency_id': expense.agency_id.name,
                                'project_id': expense.project_id.name,
                                'agency_category': expense.agency_category.name,
                                'payment_type': expense.payment_type,
                                'expense_date': expense.expense_date,
                                'type': 'Expense',
                                'total_cost': expense.project_id.cost_price,
                                'customer_amount': expense.project_id.customer_amount,
                                'pending': expense.project_id.balance_receivable,
                                'total_amount': expense.project_id.total_paid,
                                'total_amount_expense': expense.total_amount,
                                'currency_id': expense.currency_id.symbol,
                                'remark': expense.remark
                            })
                            project_data['total_paid'] += expense_amount

                    for vendor in vendor_projects_all:
                        for payment_line in vendor.project_form_id:
                            if vendor.vendor_id == agency:
                                vendor_amount = payment_line.vendor_payment
                                project_data['vendor_ids'].append({
                                    'agency_id': vendor.vendor_id.name,
                                    'type': 'Debit',
                                    'agency_category': payment_line.agency_category.name,
                                    'payment_type': vendor.name,
                                    'payment_date': vendor.payment_date,
                                    'project_id': payment_line.project_id.name,
                                    'total_cost': payment_line.project_id.cost_price,
                                    'paid_amount': payment_line.project_id.total_paid,
                                    'pending': payment_line.project_id.balance_receivable,
                                    'total_amount_vendor': payment_line.vendor_payment,
                                    'currency_id': payment_line.currency_id.symbol,
                                    'invoice_number': vendor.invoice_number
                                })
                                project_data['total_vendor'] += vendor_amount
                    # Append project data to the report list only if it contains expenses or vendor data
                    if project_data['expenses_ids'] or project_data['vendor_ids']:
                        report_data_all.append(project_data)

                return {
                    'report_data': report_data_all,
                }
            return None
    def _group_by_project(self, report_data):
        """
        Groups expenses and vendors by project and fetches project totals from `project.interior`.
        """
        grouped = defaultdict(lambda: {
            'expenses_ids': [],
            'vendor_ids': [],
            'total_ctc': 0.0,
            'total_paid': 0.0,
            'total_remaining': 0.0,
            'currency_id': '',
        })

        for entry in report_data:
            # Handle expenses
            for exp in entry.get('expenses_ids', []):
                project_name = exp.get('project_id') or 'No Project'
                grouped[project_name]['expenses_ids'].append(exp)
                grouped[project_name]['currency_id'] = exp.get('currency_id', '')

            # Handle vendors
            for ven in entry.get('vendor_ids', []):
                project_name = ven.get('project_id') or 'No Project'
                grouped[project_name]['vendor_ids'].append(ven)
                grouped[project_name]['currency_id'] = ven.get('currency_id', '')

        # Fetch project model data once per project
        result = []
        for project_name, data in grouped.items():
            # Get the actual project.interior record by name
            project = self.env['project.interior'].search([('name', '=', project_name)], limit=1)
            data['project_id'] = project_name
            data['total_ctc'] = project.total_ctc if project else 0.0
            data['total_paid'] = project.total_paid if project else 0.0
            data['total_remaining'] = data['total_ctc'] - data['total_paid'] if project else 0.0
            result.append(data)

        return result

    def agency_generate_excel_report(self):
        if self.start_date > self.end_date:
            raise UserError('Start date cannot be later than end date.')

        agencies = self.agency_ids or self.env['res.agency'].search([])
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Agency Report")

        # Excel Styles
        bold = workbook.add_format({'bold': True})
        currency_fmt = workbook.add_format({'num_format': '"$"#,##0'})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#DDEBF7', 'border': 1})
        section_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#4F81BD', 'font_color': 'white'})

        row = 0
        sheet.write(row, 0, "Agency Reports", bold)
        row += 1
        sheet.write(row, 0, "Start Date:", bold)
        sheet.write(row, 1, str(self.start_date))
        sheet.write(row, 3, "End Date:", bold)
        sheet.write(row, 4, str(self.end_date))
        row += 2

        for agency in agencies:
            data = self._generate_data(self.start_date, self.end_date, agency)
            project_groups = self._group_by_project(data.get('report_data', []))

            agency_name = agency.name
            total_ctc = data.get('TOTAL_CTC', 0.0)
            total_paid = data.get('TOTAL_paid', 0.0)
            total_remaining = total_ctc - total_paid
            total_cash = data.get('total_cash_payment', 0.0)
            total_bank = data.get('total_bank_payment', 0.0)

            # Agency Summary
            sheet.write(row, 0, "Agency Name:", bold)
            sheet.write(row, 1, agency_name)
            sheet.write(row, 3, "Total CTC:", bold)
            sheet.write_number(row, 4, total_ctc, currency_fmt)
            sheet.write(row, 6, "Total Remaining:", bold)
            sheet.write_number(row, 7, total_remaining, currency_fmt)
            row += 1
            sheet.write(row, 0, "Total Paid:", bold)
            sheet.write_number(row, 1, total_paid, currency_fmt)
            sheet.write(row, 3, "Total Cash:", bold)
            sheet.write_number(row, 4, total_cash, currency_fmt)
            sheet.write(row, 6, "Total Bank:", bold)
            sheet.write_number(row, 7, total_bank, currency_fmt)
            row += 2

            for project in project_groups:
                project_name = project.get('project_id', '')
                project_ctc = project.get('total_ctc', 0.0)
                project_paid = project.get('total_paid', 0.0)
                project_remaining = project_ctc - project_paid

                # Project Header
                sheet.write(row, 0, f"Project Name: {project_name}", section_fmt)
                row += 1
                sheet.write(row, 0, "Total Paid:", bold)
                sheet.write_number(row, 1, project_paid)
                sheet.write(row, 3, "Total CTC:", bold)
                sheet.write_number(row, 4, project_ctc)
                sheet.write(row, 6, "Total Remaining:", bold)
                sheet.write_number(row, 7, project_remaining)
                row += 2

                # Table Header
                headers = ["Date", "Agency Category", "Invoice", "Payment Type", "Type", "Amount Paid"]
                for col, header in enumerate(headers):
                    sheet.write(row, col, header, header_fmt)
                row += 1

                # Expenses
                for exp in project.get('expenses_ids', []):
                    sheet.write(row, 0, str(exp.get('expense_date', '')))
                    sheet.write(row, 1, exp.get('agency_category', ''))
                    sheet.write(row, 2, exp.get('remark', ''))
                    sheet.write(row, 3, exp.get('payment_type', ''))
                    sheet.write(row, 4, exp.get('type', 'Expense'))  # Explicit type
                    sheet.write_number(row, 5, exp.get('total_amount_expense', 0.0), currency_fmt)
                    row += 1

                # Vendors
                for ven in project.get('vendor_ids', []):
                    sheet.write(row, 0, str(ven.get('payment_date', '')))
                    sheet.write(row, 1, ven.get('agency_category', ''))
                    sheet.write(row, 2, ven.get('invoice_number', ''))
                    sheet.write(row, 3, ven.get('payment_type', ''))
                    sheet.write(row, 4, ven.get('type', 'Debit'))  # Explicit type
                    sheet.write_number(row, 5, ven.get('total_amount_vendor', 0.0), currency_fmt)
                    row += 1

                row += 2  # Space between projects

            row += 2  # Space between agencies

        # Auto-fit columns
        for col in range(8):
            sheet.set_column(col, col, 22)

        workbook.close()
        output.seek(0)
        excel_data = output.read()

        # Save as attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'agency_report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(excel_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self'
        }