from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import io
import xlsxwriter
from datetime import datetime, date


class ProjectWizard(models.TransientModel):
    _name = 'project.report'
    _description = 'Report Wizard'

    def _default_start_date(self):
        """Returns the first day of the current month."""
        today = date.today()
        return today.replace(day=1)

    def _default_end_date(self):
        """Returns today's date."""
        return date.today()

    start_date = fields.Date(string='Start Date', required=True, default=_default_start_date)
    end_date = fields.Date(string='End Date', required=True, default=_default_end_date)
    project_id = fields.Many2many('project.interior', string="Projects")

    @api.model
    def default_get(self, fields):
        res = super(ProjectWizard, self).default_get(fields)
        return res

    def generate_report(self):
        # Ensure the start date is not after the end date
        if self.start_date > self.end_date:
            raise UserError('Start date cannot be later than end date.')

        company_logo = self.env.company.logo
        # Example: Generate a report based on the date range
        report_data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'company_logo': company_logo,
            'data': self._generate_data(self.start_date, self.end_date)
        }

        # Return the report data (or print it, save it as PDF, etc.)
        return self.env.ref('saara_spaces_models.project_report_action_template').report_action(self, data=report_data)

    def generate_excel_report(self):
        if self.start_date > self.end_date:
            raise UserError('Start date cannot be later than end date.')

        company = self.env.company
        currency = company.currency_id.symbol or '$'

        projects_data = self._generate_data(self.start_date, self.end_date)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Project Report")

        # === FORMATS ===
        header_bg = '#4F81BD'
        alt_fill_color = '#F2F2F2'

        header_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'bg_color': header_bg, 'font_color': 'white', 'align': 'center',
            'valign': 'vcenter'
        })
        date_fmt = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd', 'align': 'center'})
        alt_date_fmt = workbook.add_format(
            {'border': 1, 'num_format': 'yyyy-mm-dd', 'align': 'center', 'bg_color': alt_fill_color})

        currency_fmt = workbook.add_format({'border': 1, 'num_format': f'"{currency}" #,##0.00', 'align': 'right'})
        alt_currency_fmt = workbook.add_format(
            {'border': 1, 'num_format': f'"{currency}" #,##0.00', 'align': 'right', 'bg_color': alt_fill_color})

        text_fmt = workbook.add_format({'border': 1, 'align': 'left'})
        alt_text_fmt = workbook.add_format({'border': 1, 'align': 'left', 'bg_color': alt_fill_color})

        bold = workbook.add_format({'bold': True})
        bold_border = workbook.add_format({'bold': True, 'border': 1})

        row = 0

        # === Report Header ===
        sheet.merge_range(row, 0, row, 6,
                          f"Project Payment and Expense Summary - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                          bold)
        row += 2

        sheet.write(row, 0, "Start Date:", bold)
        sheet.write(row, 1, str(self.start_date))
        sheet.write(row, 2, "End Date:", bold)
        sheet.write(row, 3, str(self.end_date))
        row += 2

        for project in projects_data:
            # === Project Summary ===
            sheet.write(row, 0, "Project:", bold)
            sheet.write(row, 1, project.get('project_name', ''))
            sheet.write(row, 2, "Total Cost:", bold)
            sheet.write_number(row, 3, project.get('cost_price', 0), currency_fmt)
            sheet.write(row, 4, "Total Paid:", bold)
            sheet.write_number(row, 5, project.get('project_total', 0), currency_fmt)
            row += 1

            sheet.write(row, 0, "Customer Name:", bold)
            sheet.write(row, 1, project.get('customer_id', ''))
            sheet.write(row, 2, "Total Received:", bold)
            sheet.write_number(row, 3, project.get('customer_amount', 0), currency_fmt)
            sheet.write(row, 4, "CTC:", bold)
            sheet.write_number(row, 5, project.get('total_ctc', 0), currency_fmt)
            row += 2

            # === Expenses Section ===
            sheet.write(row, 0, "Expenses:", bold_border)
            row += 1
            headers = ["Expense Date", "Agency / Person Name", "Work Category", "Invoice", "Payment Type", "Type",
                       "Amount"]
            for col, header in enumerate(headers):
                sheet.write(row, col, header, header_fmt)
            row += 1

            for idx, exp in enumerate(project.get('expenses', [])):
                fmt_date = date_fmt if idx % 2 == 0 else alt_date_fmt
                fmt_text = text_fmt if idx % 2 == 0 else alt_text_fmt
                fmt_currency = currency_fmt if idx % 2 == 0 else alt_currency_fmt

                sheet.write_datetime(row, 0, exp.get('expense_date'), fmt_date)
                sheet.write(row, 1, exp.get('agency_id') or exp.get('person_name', ''), fmt_text)
                sheet.write(row, 2, exp.get('work_catg', ''), fmt_text)
                sheet.write(row, 3, exp.get('remark', ''), fmt_text)
                sheet.write(row, 4, exp.get('payment_type', ''), fmt_text)
                sheet.write(row, 5, "Expenses", fmt_text)
                sheet.write_number(row, 6, exp.get('total_amount', 0), fmt_currency)
                row += 1

            # === Vendor Payments Section (as Debit) ===
            for idx, pay in enumerate(project.get('vendor_payments', [])):
                fmt_date = date_fmt if idx % 2 == 0 else alt_date_fmt
                fmt_text = text_fmt if idx % 2 == 0 else alt_text_fmt
                fmt_currency = currency_fmt if idx % 2 == 0 else alt_currency_fmt

                sheet.write_datetime(row, 0, pay.get('payment_date'), fmt_date)
                sheet.write(row, 1, pay.get('vendor_id', ''), fmt_text)
                sheet.write(row, 2, pay.get('agency_category', ''), fmt_text)
                sheet.write(row, 3, pay.get('invoice_number', ''), fmt_text)
                sheet.write(row, 4, pay.get('payment_method', ''), fmt_text)
                sheet.write(row, 5, "Debit", fmt_text)
                sheet.write_number(row, 6, pay.get('vendor_payment', 0), fmt_currency)
                row += 1

            row += 1

            # === Customer Payments Section ===
            sheet.write(row, 0, "Customer Payments:", bold_border)
            row += 1
            cust_headers = ["Payment Date", "Invoice", "Payment Type", "Payment"]
            for col, header in enumerate(cust_headers):
                sheet.write(row, col, header, header_fmt)
            row += 1

            for idx, cust_pay in enumerate(project.get('customer_payments', [])):
                fmt_date = date_fmt if idx % 2 == 0 else alt_date_fmt
                fmt_text = text_fmt if idx % 2 == 0 else alt_text_fmt
                fmt_currency = currency_fmt if idx % 2 == 0 else alt_currency_fmt

                sheet.write_datetime(row, 0, cust_pay.get('payment_date'), fmt_date)
                sheet.write(row, 1, cust_pay.get('sale_invoice', ''), fmt_text)
                sheet.write(row, 2, cust_pay.get('name', ''), fmt_text)
                sheet.write_number(row, 3, cust_pay.get('customer_payment', 0), fmt_currency)
                row += 1

            row += 3  # Add some space before next project

        # Set column widths nicely
        sheet.set_column(0, 0, 15)  # Dates
        sheet.set_column(1, 1, 22)  # Names
        sheet.set_column(2, 2, 15)  # Categories
        sheet.set_column(3, 3, 20)  # Invoice / Remarks
        sheet.set_column(4, 4, 15)  # Payment type
        sheet.set_column(5, 5, 10)  # Type (Expenses/Debit)
        sheet.set_column(6, 6, 15)  # Amount

        workbook.close()
        output.seek(0)
        excel_data = output.read()
        # Create attachment for download
        attachment = self.env['ir.attachment'].create({
            'name': 'project_report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(excel_data),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self'
        }

    def _generate_data(self, start_date, end_date):
        # Fetch the records from the project.interior model
        today = date.today()
        if self.project_id:
            projects = self.env['project.interior'].search(
                [('create_date', '>=', start_date), ('create_date', '<=', end_date), ('id', '=', self.project_id.id)])
        else:
            projects = self.env['project.interior'].search(
                [('create_date', '>=', start_date), ('create_date', '<=', end_date)])
        report_data_new = []

        for project in projects:
            project_data = {
                'project_name': project.name,
                'project_total': project.total_paid,
                'project_ctc': project.total_paid,
                'currency_id': project.currency_id.symbol,
                'customer_amount': project.customer_amount,
                'cost_price': project.cost_price,
                'total_ctc': project.total_ctc,
                'customer_id': project.customer_id.name,
                'vendor_payments': [],
                'customer_payments': [],
                'expenses': [],
            }

            # Loop through vendor payments (agency_payment_id)
            for payment in project.agency_payment_id:
                project_data['vendor_payments'].append({
                    'payment_method': payment.name,
                    'agency_category': payment.agency_category.name,
                    'vendor_id': payment.vendor_id.name,
                    'payment_date': payment.payment_date,
                    'vendor_payment': payment.vendor_payment,
                    'currency_id': payment.currency_id.symbol,
                    'invoice_number': payment.invoice_number
                })

            # Loop through customer payments (payments_ids)
            for payment in project.payments_ids:
                project_data['customer_payments'].append({
                    'customer_id': payment.customer_id.name,
                    'payment_date': payment.payment_date,
                    'customer_payment': payment.customer_payment,
                    'name': payment.name,
                    'currency_id': payment.currency_id.symbol,
                    'sale_invoice': payment.sale_invoice
                })

            # Loop through expenses (expenses_ids)
            for expense in project.expenses_ids:
                project_data['expenses'].append({
                    'category_id': expense.category_id.name,
                    'agency_id': expense.agency_id.name,
                    'expense_date': expense.expense_date,
                    'total_amount': expense.total_amount,
                    'name': expense.name,
                    'work_catg': expense.agency_category.name,
                    'payment_type': expense.payment_type,
                    'currency_id': expense.currency_id.symbol,
                    'person_name': expense.person_name,
                    'remark': expense.remark
                })
            report_data_new.append(project_data)
        return report_data_new

    def _generate_data_mobile(self, start_date, end_date, project_id):
        # Fetch the records from the project.interior model
        print("=============project_idproject_id========",project_id)
        if project_id:
            print("============ifffff")
            projects = self.env['project.interior'].sudo().search(
                [('id', '=', project_id), ('create_date', '>=', start_date), ('create_date', '<=', end_date)])
        else:
            print("else--------------")
            projects = self.env['project.interior'].search(
                [('create_date', '>=', start_date), ('create_date', '<=', end_date)])
        report_data_new = []
        for project in projects:
            project_data = {
                'project_name': project.name,
                'project_total': project.total_paid,
                'project_ctc': project.total_paid,
                'currency_id': project.currency_id.symbol,
                'customer_amount': project.customer_amount,
                'cost_price': project.cost_price,
                'total_ctc': project.total_ctc,
                'customer_id': project.customer_id.name,
                'vendor_payments': [],
                'customer_payments': [],
                'expenses': [],
            }

            # Loop through vendor payments (agency_payment_id)
            for payment in project.agency_payment_id:
                project_data['vendor_payments'].append({
                    'payment_method': payment.name,
                    'agency_category': payment.agency_category.name,
                    'vendor_id': payment.vendor_id.name,
                    'payment_date': payment.payment_date,
                    'vendor_payment': payment.vendor_payment,
                    'currency_id': payment.currency_id.symbol,
                    'invoice_number': payment.invoice_number
                })

            # Loop through customer payments (payments_ids)
            for payment in project.payments_ids:
                project_data['customer_payments'].append({
                    'customer_id': payment.customer_id.name,
                    'payment_date': payment.payment_date,
                    'customer_payment': payment.customer_payment,
                    'name': payment.name,
                    'currency_id': payment.currency_id.symbol,
                    'sale_invoice': payment.sale_invoice
                })

            # Loop through expenses (expenses_ids)
            for expense in project.expenses_ids:
                project_data['expenses'].append({
                    'category_id': expense.category_id.name,
                    'agency_id': expense.agency_id.name,
                    'expense_date': expense.expense_date,
                    'total_amount': expense.total_amount,
                    'name': expense.name,
                    'work_catg': expense.agency_category.name,
                    'payment_type': expense.payment_type,
                    'currency_id': expense.currency_id.symbol,
                    'person_name': expense.person_name,
                    'remark': expense.remark
                })

            report_data_new.append(project_data)
        return report_data_new
