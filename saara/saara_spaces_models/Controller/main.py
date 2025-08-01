from tkinter.font import names

from odoo import http
from odoo.http import request
from collections import defaultdict
import json
import base64
import jwt
from werkzeug.exceptions import Unauthorized
from odoo.addons.website_sale.controllers.main import QueryURL
from odoo.addons.portal.controllers.portal import pager as portal_pager
import ast


class ExpenseChartController(http.Controller):

    @http.route("/api/login", auth="public", type="json", methods=["POST"], csrf=False)
    def login(self, **post):
        login = post.get('email')  # Typo corrected from 'emil' to 'email'
        password = post.get('password')

        if not login or not password:
            return {
                "success": False,
                "status_code": 400,
                "message": "Missing credentials",
                "errors": {
                    "message": "Email and Password are required"
                }
            }
        try:
            # Authenticate using internal Odoo method
            uid = request.session.authenticate(request.db, login, password)
            user = request.env['res.users'].sudo().browse(uid)
            # Generate token
            jwt_token = jwt.encode(
                {"login": login, "user_id": user.id},
                key='secret',
                algorithm='HS256'
            )
            # Store token (optional, if you want to track)
            user.write({
                "jwt_token": jwt_token
            })
            return {
                "success": True,
                "status_code": 200,
                "message": "Login successful",
                "data": {
                    "jwt_token": jwt_token,
                    "employee": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.login,
                        "password": base64.b64encode(password.encode("utf-8")).decode("utf-8"),
                    }
                }
            }
        except Unauthorized:
            return {
                "success": False,
                "status_code": 401,
                "message": "Login failed",
                "errors": {
                    "message": "Email or Password is incorrect"
                }
            }

    @http.route("/api/profile", auth="public", type="http", methods=["GET"], csrf=False)
    def user_profile(self, **post):
        jwt_token = request.httprequest.headers['Jwtoken']
        employee = http.request.env['res.users'].sudo().search([('jwt_token', '=', jwt_token)])

        if employee:
            is_super_admin = employee.has_group('saara_spaces_models.group_super_admin')
            is_admin = employee.has_group('saara_spaces_models.group_admin')
            is_employee = employee.has_group('saara_spaces_models.group_employee')
            return json.dumps({"success": True,
                               "status_code": 200,
                               "message": "Get employee profile data ",
                               "params": "",
                               "data": {
                                   "profile_img": employee.image_1920,
                                   "employee": {
                                       'id': employee.id,
                                       "name": employee.name,
                                       "email": employee.login,
                                       "phone": employee.partner_id.phone,
                                       "mobile": employee.partner_id.mobile,
                                       "password": base64.b64encode(employee.new_password.encode("utf-8")),
                                       "is_super_admin": is_super_admin if is_super_admin else False,
                                       "is_admin": is_admin if is_admin else False,
                                       "is_employee": is_employee if is_employee else False
                                   },
                               }
                               }, default=str)
        else:
            return json.dumps(
                {
                    "success": "false",
                    "status_code": 401,
                    "message": "Unauthenticated User"
                }
            )

    @http.route("/api/create/customer", auth="public", type="http", methods=["POST"], csrf=False)
    def CreateCustomer(self, **post):
        name = post.get('name', '').title()
        street = post.get('street', '').title()
        street2 = post.get('street2', '').title()
        city = post.get('city', '').title()
        state_id = post.get('state_id')
        zip = post.get('zip')
        phone = post.get('phone')
        mobile = post.get('mobile')
        email = post.get('email')
        image_1998 = post.get('image_1998')
        tag_id = post.get('tag_id')
        state = request.env['res.country.state'].sudo().search([('id', '=', state_id)])
        customer_name = request.env['res.customer'].sudo().search([('name', '=', name)])
        if customer_name:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "The name must be unique"
            })
        else:
            if not image_1998:
                customer_id = request.env['res.customer'].sudo().create({
                    'name': name,
                    'street': street,
                    'street2': street2 if street2 else False,
                    'city': city,
                    'state_id': state.id,
                    'zip': zip,
                    'phone': phone if phone else False,
                    'mobile': mobile,
                    'email': email if email else False,
                    'tag_id': tag_id if tag_id else False,
                })
                return json.dumps({
                    "data": {
                        'id': customer_id.id
                    },
                    "success": True,
                    "status_code": 200,
                    "message": "Success Create Customer"
                })
            else:
                content = image_1998.read()
                base64e = base64.b64encode(content)
                customer_id = request.env['res.customer'].sudo().create({
                    'name': name,
                    'street': street,
                    'street2': street2 if street2 else False,
                    'city': city,
                    'state_id': state.id,
                    'zip': zip,
                    'phone': phone if phone else False,
                    'mobile': mobile,
                    'email': email if email else False,
                    'image_1998': base64e if base64e else False,
                    'tag_id': tag_id if tag_id else False,
                })
            return json.dumps({
                "data": {
                    'id': customer_id.id
                },
                "success": True,
                "status_code": 200,
                "message": "Success Create Customer"
            })

    @http.route("/api/create/Agency", auth="public", type="http", methods=["POST"], csrf=False)
    def CreateAgency(self, **post):
        name = post.get('name', '').title()
        street = post.get('street', '').title()
        street2 = post.get('street2', '').title()
        city = post.get('city', '').title()
        state_id = post.get('state_id')
        zip = post.get('zip')
        phone = post.get('phone')
        mobile = post.get('mobile')
        poc_name = post.get('poc_name', '').title()
        gst_required = post.get('gst_required')
        gst_no = post.get('gst_no')
        email = post.get('email')
        image_1998 = post.get('image_1998')
        tag_id = post.get('tag_id')
        state = request.env['res.country.state'].sudo().search([('id', '=', state_id)])

        agency_name = request.env['res.agency'].sudo().search([('name', '=', name)])
        if agency_name:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "The name must be unique"
            })
        else:
            if image_1998:
                content = image_1998.read()
                base64e = base64.b64encode(content)
                agency_id = request.env['res.agency'].sudo().create({
                    'name': name,
                    'street': street,
                    'street2': street2 if street2 else False,
                    'city': city,
                    'state_id': state.id,
                    'zip': zip,
                    'phone': phone if phone else False,
                    'mobile': mobile,
                    'poc_name': poc_name,
                    'gst_required': gst_required,
                    'gst_no': gst_no,
                    'email': email if email else False,
                    'image_1998': base64e if base64e else False,
                    'tag_id': tag_id if tag_id else 'agency',
                })
                return json.dumps({
                    "data": {
                        'id': agency_id.id
                    },
                    "success": True,
                    "status_code": 200,
                    "message": "Success Create Agency"
                })
            else:
                agency_id = request.env['res.agency'].sudo().create({
                    'name': name,
                    'street': street,
                    'street2': street2 if street2 else False,
                    'city': city,
                    'state_id': state.id,
                    'zip': zip,
                    'phone': phone if phone else False,
                    'mobile': mobile,
                    'poc_name': poc_name,
                    'gst_required': gst_required,
                    'gst_no': gst_no,
                    'email': email if email else False,
                    'tag_id': tag_id if tag_id else 'agency',
                })
                return json.dumps({
                    "data": {
                        'id': agency_id.id
                    },
                    "success": True,
                    "status_code": 200,
                    "message": "Success Create Agency"
                })

    @http.route("/api/create/receivable", auth="public", type="http", methods=["POST"], csrf=False)
    def CreatePaymentReceivable(self, **post):
        payment_method = post.get('payment_method')
        sale_invoice = post.get('sale_invoice')
        interior_project_id = post.get('interior_project_id')
        payment_date = post.get('payment_date')
        customer_payment = post.get('customer_payment')
        project_id = request.env['project.interior'].sudo().search([('id', '=', interior_project_id)])

        if not payment_method:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "Not Create Receivable"
            })
        else:
            receivable_id = request.env['payment.method'].sudo().create({
                'name': payment_method,
                'sale_invoice': sale_invoice,
                'interior_project_id': project_id.id,
                'customer_id': project_id.customer_id.id,
                'payment_date': payment_date,
                'customer_payment': customer_payment
            })
        return json.dumps({
            "data": {
                "receivable_id": receivable_id.id
            },
            "success": True,
            "status_code": 200,
            "message": "Success Create Receivable"
        })

    @http.route("/api/create/payable", auth="public", type="http", methods=["POST"], csrf=False)
    def CreateVendorPayable(self, **post):
        payment_method = post.get('payment_method')
        invoice_number = post.get('invoice_number')
        agency = post.get('agency')
        payment_date = post.get('payment_date')
        project_ids = post.get('interior_project_id')
        agency_categories = post.get('agency_category')
        vendor_payments = post.get('vendor_payment')

        # Convert project_ids, agency_categories, and vendor_payments to lists
        try:
            if isinstance(project_ids, str):
                project_ids = json.loads(project_ids)
            if isinstance(agency_categories, str):
                agency_categories = json.loads(agency_categories)
            if isinstance(vendor_payments, str):
                vendor_payments = json.loads(vendor_payments)
        except Exception as e:
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": f"Invalid JSON format in lists: {str(e)}"
            })

        # Validate lists are present and of equal length
        if not (project_ids and agency_categories and vendor_payments):
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "Missing project_ids, agency_categories, or vendor_payments"
            })

        if not (len(project_ids) == len(agency_categories) == len(vendor_payments)):
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": "project_ids, agency_categories, and vendor_payments must be of equal length"
            })

        # Fetch agency record
        agency_id = request.env['res.agency'].sudo().search([('id', '=', int(agency))], limit=1)
        if not agency_id:
            return json.dumps({
                "success": False,
                "status_code": 404,
                "message": "Agency not found"
            })

        # Prepare lines
        form_lines = []
        for idx in range(len(project_ids)):
            project = request.env['project.interior'].sudo().search([('id', '=', project_ids[idx])], limit=1)
            category = request.env['agency.category'].sudo().search([('id', '=', agency_categories[idx])], limit=1)
            payment = vendor_payments[idx]

            if project and category:
                form_lines.append((0, 0, {
                    'project_id': project.id,
                    'agency_category': category.id,
                    'vendor_payment': payment
                }))

        if not form_lines:
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": "No valid form lines to create"
            })

        # Create the vendor.payment.method record
        payable = request.env['vendor.payment.method'].sudo().create({
            'name': payment_method,
            'invoice_number': invoice_number,
            'vendor_id': agency_id.id,
            'payment_date': payment_date,
            're_write': True,
            'project_form_id': form_lines
        })

        return json.dumps({
            "data": {
                "payable_id": payable.id
            },
            "success": True,
            "status_code": 200,
            "message": "Payable created with multiple project lines"
        })

    @http.route("/api/create/expenses", auth="public", type="http", methods=["POST"], csrf=False)
    def CreateVendorExpenses(self, **post):
        name = post.get('name', '').title()
        expenses_category_id = post.get('expenses_category_id')
        project_id = post.get('project_id')
        is_person = post.get('is_person')
        person_name = post.get('person_name', '').title()
        agency_id = post.get('agency_id')
        agency_category_id = post.get('work_agency')
        expense_date = post.get('expense_date')
        total_amount = post.get('total_amount')
        paid_by_employee_id = post.get('paid_by_employee_id')
        payment_type = post.get('payment_type')
        remark = post.get('remark')
        expenses_category = request.env['expenses.category'].sudo().search([('id', '=', expenses_category_id)])
        agency_category = request.env['agency.category'].sudo().search([('id', '=', agency_category_id)])
        project = request.env['project.interior'].sudo().search([('id', '=', project_id)])
        agency = request.env['res.agency'].sudo().search([('id', '=', agency_id)])
        user_id = request.env['res.users'].sudo().search([('id', '=', paid_by_employee_id)])
        expenses_name = request.env['project.expenses'].sudo().search([('name', '=', name)])
        if expenses_name:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "The name must be unique"
            })
        else:
            expenses_id = request.env['project.expenses'].sudo().create({
                'name': name,
                'category_id': expenses_category.id,
                'project_id': project.id,
                'is_person': is_person if is_person else False,
                'person_name': person_name if person_name else False,
                'agency_id': agency.id,
                'agency_category': agency_category.id,
                'expense_date': expense_date,
                'total_amount': total_amount,
                'paid_by_employee_id': user_id.id,
                'payment_type': payment_type,
                'remark': remark if remark else False
            })
            payable_id = request.env['vendor.payment.method'].sudo().create({
                'name': payment_type,
                'expense_id': expenses_id.id,
                'vendor_id': agency.id,
                'interior_project_id': project.id,
                'payment_date': expense_date,
                'expenses': True,
            })
            line = payable_id.project_form_id[:1]
        return json.dumps({
            "data": {
                "expenses_id": expenses_id.id,
                'payable_id': payable_id.id
            },
            "success": True,
            "status_code": 200,
            "message": "Success Create Expenses"
        })

    @http.route("/api/expenses/category/list", auth="public", type="http", methods=["GET"], csrf=False)
    def ExpensesCategory(self):
        expenses_ids = request.env['expenses.category'].sudo().search([])
        expenses = []
        for expense in expenses_ids:
            expenses.append({
                'id': expense.id,
                'name': expense.name,
            })
        return json.dumps({
            'Expenses_Category': expenses,
            "success": True,
            "status_code": 200,
            "message": "Success Get Expenses Category"
        })

    @http.route("/api/agency/category/list", auth="public", type="http", methods=["GET"], csrf=False)
    def AgencyWorkCategory(self):
        agency_work_ids = request.env['agency.category'].sudo().search([])
        agency_list = []
        for agency in agency_work_ids:
            agency_list.append({
                'id': agency.id,
                'name': agency.name,
            })
        return json.dumps({
            'Expenses_Category': agency_list,
            "success": True,
            "status_code": 200,
            "message": "Success Get Agency Work Category"
        })

    @http.route(['/api/project/engineering/list', '/api/project/engineering/list/page/<int:page>'],
                auth="public", type="http", methods=["GET"], csrf=False)
    def ProjectPagination(self, page=1, order=None, **post):
        try:
            page = int(page) if page else 1
        except ValueError:
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": "Invalid page number"
            })
        order = post.get('order') or order or "id desc"
        url = "/api/project/engineering/list"
        project_count = request.env['project.interior'].sudo().search_count([])
        ppg = 10
        offset = (page - 1) * ppg
        pager = portal_pager(
            url=url,
            total=project_count,
            page=page,
            step=ppg,
            url_args=post
        )
        project_name = request.env['project.interior'].sudo().search([], offset=offset, order=order)
        if project_name:
            data = []
            for project_id in project_name:
                data.append({
                    'id': project_id.id,
                    'name': project_id.name,
                    'street': project_id.street,
                    'street2': project_id.street2 if project_id.street2 else None,
                    'state_id': project_id.state_id.name,
                    'zip': project_id.zip,
                    'country_id': project_id.country_id.name,
                    'poc_name': project_id.poc_name,
                    'contact_information': project_id.contact_information,
                    'customer_id': project_id.customer_id.name,
                    'cost_price': project_id.cost_price,
                    'buffer': project_id.buffer,
                    'total_amount_quotation': project_id.total_amount,
                    'total_ctc': project_id.total_ctc,
                    'customer_amount': project_id.customer_amount,
                    'balance_receivable': project_id.balance_receivable,
                    'total_paid': project_id.total_paid,
                    'pending_ctc': project_id.pending_ctc
                })
            return json.dumps({
                "success": True,
                "status_code": 200,
                "message": "Get All Project ",
                "data": {
                    'data': data,
                    'page_count': pager['page_count'],
                    'current_page': page,
                }
            }, default=str)
        else:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "Data Not Found!"
            })

    @http.route(['/api/customer/list', '/api/customer/list/page/<int:page>'],
                auth="public", type="http", methods=["GET"], csrf=False)
    def customer_list(self, page=1, order=None, **post):
        try:
            page = int(page) if page else 1
        except ValueError:
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": "Invalid page number"
            })
        order = post.get('order') or order or "id desc"
        url = "/api/customer/list"
        customer_count = request.env['res.customer'].sudo().search_count([])
        ppg = 10
        offset = (page - 1) * ppg

        pager = portal_pager(
            url=url,
            total=customer_count,
            page=page,
            step=ppg,
            url_args=post
        )
        customers = request.env['res.customer'].sudo().search([], offset=offset, limit=ppg, order=order)
        if customers:
            customer_list = []
            for customer in customers:
                customer_list.append({
                    'customer_id': customer.id,
                    'customer_name': customer.name,
                    'street': customer.street,
                    'street2': customer.street2 if customer.street2 else None,
                    'state_id': customer.state_id.name,
                    'zip': customer.zip,
                    'country_id': customer.country_id.name,
                    'phone': customer.phone if customer.phone else None,
                    'mobile': customer.mobile,
                    'email': customer.email if customer.email else None,
                    'note': customer.note if customer.note else None,
                    'tag_id': customer.tag_id if customer.tag_id else None
                })

            return json.dumps({
                "success": True,
                "status_code": 200,
                "message": "Success - Customers retrieved",
                "data": {
                    'customers': customer_list,
                    'page_count': pager['page_count'],
                    'current_page': page,
                    'total_customer': customer_count
                }
            }, default=str)
        else:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "No customer data found!"
            })

    @http.route(['/api/agency/list', '/api/agency/list/page/<int:page>'], auth="public", type="http", methods=["GET"],
                csrf=False)
    def AgencyList(self, page=1, order=None, **post):
        try:
            page = int(page) if page else 1
        except ValueError:
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": "Invalid page number"
            })
        order = post.get('order') or order or "id desc"
        url = "/api/agency/list"
        agency_count = request.env['res.agency'].sudo().search_count([])
        ppg = 10
        offset = (page - 1) * ppg

        pager = portal_pager(
            url=url,
            total=agency_count,
            page=page,
            step=ppg,
            url_args=post
        )
        agency_id = request.env['res.agency'].sudo().search([], offset=offset, order=order)
        if agency_id:
            agency_list = []
            for agency in agency_id:
                agency_list.append({
                    'agency_id': agency.id,
                    'agency_name': agency.name,
                    'customer_name': agency.name,
                    'street': agency.street,
                    'street2': agency.street2 if agency.street2 else None,
                    'state_id': agency.state_id.name,
                    'zip': agency.zip,
                    'country_id': agency.country_id.name,
                    'poc_name': agency.poc_name if agency.poc_name else None,
                    'phone': agency.phone if agency.phone else None,
                    'mobile': agency.mobile,
                    'email': agency.email if agency.email else None,
                    'note': agency.note if agency.note else None
                })
            return json.dumps({
                "success": True,
                "status_code": 200,
                "message": "Success Get All Agency ",
                "data": {
                    'data': agency_list,
                    'page_count': pager['page_count'],
                    'current_page': page,
                    'total_agency': agency_count
                }
            }, default=str)
        else:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "Data Not Found!"
            })

    @http.route(['/api/receivable/list', '/api/receivable/list/page/<int:page>'], auth="public", type="http",
                methods=["GET"], csrf=False)
    def ReceivableList(self, page=1, order=None, **post):
        try:
            page = int(page) if page else 1
        except ValueError:
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": "Invalid page number"
            })
        order = post.get('order') or order or "id desc"
        url = "/api/receivable/list"
        receivable_count = request.env['payment.method'].sudo().search_count([])
        ppg = 10
        offset = (page - 1) * ppg

        pager = portal_pager(
            url=url,
            total=receivable_count,
            page=page,
            step=ppg,
            url_args=post
        )
        receivable_id = request.env['payment.method'].sudo().search([], offset=offset, order=order)
        if receivable_id:
            receivable = []
            for receivables in receivable_id:
                receivable.append({
                    'id': receivables.id,
                    'payment_method': receivables.name,
                    'sale_invoice': receivables.sale_invoice,
                    'project': receivables.interior_project_id.name,
                    'customer_id': receivables.customer_id.name,
                    'payment_date': receivables.payment_date,
                    'customer_payment': receivables.customer_payment
                })
            return json.dumps({
                "success": True,
                "status_code": 200,
                "message": "Success Get All Receivable ",
                "data": {
                    'data': receivable,
                    'page_count': pager['page_count'],
                    'current_page': page,
                    'total_receivable': receivable_count
                }
            }, default=str)
        else:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "Data Not Found!"
            })

    @http.route(['/api/payable/list', '/api/payable/list/page/<int:page>'], auth="public", type="http",
                methods=["GET"], csrf=False)
    def PayableList(self, page=1, order=None, **post):
        try:
            page = int(page) if page else 1
        except ValueError:
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": "Invalid page number"
            })
        order = post.get('order') or order or "id desc"
        url = "/api/payable/list"
        payable_count = request.env['vendor.payment.method'].sudo().search_count(
            [('interior_project_id', '=', False), ('expenses', '=', False)])
        ppg = 10
        offset = (page - 1) * ppg

        pager = portal_pager(
            url=url,
            total=payable_count,
            page=page,
            step=ppg,
            url_args=post
        )
        payable_id = request.env['vendor.payment.method'].sudo().search(
            [('interior_project_id', '=', False), ('expenses', '=', False)], offset=offset, order=order)
        if payable_id:
            payable_list = []
            for payables in payable_id:
                # method_str = payables
                line_list = []
                for line in payables.project_form_id:
                    line_list.append({
                        'id': line.id,
                        'project_id': line.project_id.name,
                        'agency_category': line.agency_category.name,
                        'vendor_payment': line.vendor_payment
                    })
                payable_list.append({
                    'payable_id': payables.id,
                    'payment_method': payables.name,
                    'invoice_number': payables.invoice_number,
                    'vendor_id': payables.vendor_id.name,
                    'payment_date': payables.payment_date,
                    'vendor_payment': payables.vendor_payment,
                    'expenses': payables.expenses,
                    'lines': line_list,
                })
            return json.dumps({
                "success": True,
                "status_code": 200,
                "message": "Success Get All Payable ",
                "data": {
                    'data': payable_list,
                    'page_count': pager['page_count'],
                    'current_page': page,
                    'total_payable': payable_count
                }
            }, default=str)
        else:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "Data Not Found!"
            })

    @http.route(['/api/payable/line/list', '/api/payable/line/list/page/<int:page>'], auth="public", type="http",
                methods=["GET"], csrf=False)
    def PayableLineList(self, page=1, order=None, **post):
        try:
            page = int(page) if page else 1
        except ValueError:
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": "Invalid page number"
            })
        order = post.get('order') or order or "id desc"
        url = "/api/payable/line/list"
        payable_count = request.env['vendor.payment.method'].sudo().search_count(
            [('interior_project_id', '=', False), ('expenses', '=', False)])
        ppg = 10
        offset = (page - 1) * ppg

        pager = portal_pager(
            url=url,
            total=payable_count,
            page=page,
            step=ppg,
            url_args=post
        )
        payable_id = request.env['vendor.payment.method'].sudo().search(
            [('interior_project_id', '=', False), ('expenses', '=', False)], offset=offset, order=order)
        if payable_id:
            payable_list = []
            for payables in payable_id:
                # method_str = payables
                line_list = []
                for line in payables.project_form_id:
                    line_list.append({
                        'id': line.id,
                        'project_id': line.project_id.name,
                        'agency_category': line.agency_category.name,
                        'vendor_payment': line.vendor_payment
                    })
                payable_list.append({
                    "payable_id": payables.id,
                    "lines": line_list,
                })
            return json.dumps({
                "success": True,
                "status_code": 200,
                "message": "Success Get All Payable Line",
                "data": {
                    'data': payable_list,
                    'page_count': pager['page_count'],
                    'current_page': page,
                }
            }, default=str)
        else:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "Data Not Found!"
            })

    @http.route(['/api/payable/expenses/list', '/api/payable/expenses/list/page/<int:page>'], auth="public",
                type="http", methods=["GET"], csrf=False)
    def ExpensesPayableList(self, page=1, order=None, **post):
        try:
            page = int(page) if page else 1
        except ValueError:
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": "Invalid page number"
            })
        order = post.get('order') or order or "id desc"
        url = "/api/payable/expenses/list"
        payable_count = request.env['vendor.payment.method'].sudo().search_count(
            [('expenses', '=', True), ('re_write', '=', False)])
        ppg = 10
        offset = (page - 1) * ppg
        pager = portal_pager(
            url=url,
            total=payable_count,
            page=page,
            step=ppg,
            url_args=post
        )
        payable_id = request.env['vendor.payment.method'].sudo().search(
            [('expenses', '=', True), ('re_write', '=', False)], offset=offset, order=order)
        if payable_id:
            exp_payable_list = []
            for payables in payable_id:
                exp_line_list = []
                for e_line in payables.project_form_id:
                    exp_line_list.append({
                        'id': e_line.id,
                        'project_id': e_line.project_id.name,
                        'agency_category': e_line.agency_category.name,
                        'vendor_payment': e_line.vendor_payment
                    })
                exp_payable_list.append({
                    'id': payables.id,
                    'payment_date': payables.payment_date,
                    'payment_method': payables.name,
                    'invoice_number': payables.invoice_number,
                    'vendor_id': payables.vendor_id.name,
                    'total_payment': payables.total_payment,
                    'expenses': payables.expenses,
                    'exp_lines': exp_line_list
                })
            return json.dumps({
                "success": True,
                "status_code": 200,
                "message": "Success Get All Expenses Payable ",
                "data": {
                    'data': exp_payable_list,
                    'page_count': pager['page_count'],
                    'current_page': page,
                    'total_expenses_payable': payable_count
                }
            }, default=str)
        else:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "Data Not Found!"
            })

    @http.route(['/api/expenses/list', '/api/expenses/list/page/<int:page>'], auth="public", type="http",
                methods=["GET"], csrf=False)
    def ExpensesList(self, page=1, order=None, **post):
        try:
            page = int(page) if page else 1
        except ValueError:
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": "Invalid page number"
            })
        order = post.get('order') or order or "id desc"
        url = "/api/expenses/list"
        expenses_count = request.env['project.expenses'].sudo().search_count([])
        ppg = 10
        offset = (page - 1) * ppg

        pager = portal_pager(
            url=url,
            total=expenses_count,
            page=page,
            step=ppg,
            url_args=post
        )
        expenses_id = request.env['project.expenses'].sudo().search([], offset=offset, order=order)
        if expenses_id:
            expenses_list = []
            for expense in expenses_id:
                expenses_list.append({
                    'id': expense.id,
                    'name': expense.name,
                    'expense_category': expense.category_id.name,
                    'project_id': expense.project_id.name,
                    'person_name': expense.person_name,
                    'agency_id': expense.agency_id.name,
                    'work_category': expense.agency_category.name,
                    'expense_date': expense.expense_date,
                    'total_amount': expense.total_amount,
                    'paid_by_employee_id': expense.paid_by_employee_id.name,
                    'payment_type': expense.payment_type

                })
            return json.dumps({
                "success": True,
                "status_code": 200,
                "message": "Success Get All Expenses ",
                "data": {
                    'data': expenses_list,
                    'page_count': pager['page_count'],
                    'current_page': page,
                }
            }, default=str)
        else:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "Data Not Found!"
            })

    @http.route("/api/state/list", auth="public", type="http", methods=["GET"], csrf=False)
    def StateList(self):
        state_id = request.env['res.country.state'].sudo().search([])
        state_list = []
        for state in state_id:
            state_list.append({
                'state_id': state.id,
                'state_name': state.name
            })
        return json.dumps({
            'States': state_list,
            "success": True,
            "status_code": 200,
            "message": "Success Get All State"
        })

    @http.route("/api/employee/list", auth="public", type="http", methods=["GET"], csrf=False)
    def EmployeeList(self):
        employee_id = request.env['res.users'].sudo().search([])
        employee_list = []
        if employee_id:
            for employee in employee_id:
                employee_list.append({
                    'emp_id': employee.id,
                    'emp_name': employee.name
                })
            return json.dumps({
                'Employees': employee_list,
                "success": True,
                "status_code": 200,
                "message": "Success Get All Employee"
            })

    @http.route('/api/project/engineering', auth="public", type="http",
                methods=["POST"], csrf=False)
    def CreateProjectEngineering(self, **post):
        name = post.get('name', '').title()
        street = post.get('street', '').title()
        street2 = post.get('street2', '').title()
        city = post.get('city', '').title()
        state_id = post.get('state_id')
        zip = post.get('zip')
        customer = post.get('customer')
        poc_name = post.get('poc_name', '').title()
        contact_information = post.get('contact_information')
        cost_price = post.get('cost_price')
        buffer = post.get('buffer')
        project_name = request.env['project.interior'].sudo().search([('name', '=', name)])
        state = request.env['res.country.state'].sudo().search([('id', '=', state_id)])
        customer_id = request.env['res.customer'].sudo().search([('id', '=', customer)])
        quotation_ids = post.get('quotation_ids')

        if project_name:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "The name must be unique"
            })
        else:
            project_id = request.env['project.interior'].sudo().create({
                'name': name,
                'street': street,
                'street2': street2 if street2 else False,
                'city': city,
                'state_id': state.id,
                'zip': zip,
                'customer_id': customer_id.id,
                'poc_name': poc_name,
                'contact_information': contact_information,
                'cost_price': cost_price,
                'buffer': buffer
            })
        return json.dumps({
            "data": {
                'id': project_id.id,
                'name': project_id.name,
                'poc_name': project_id.poc_name,
                'contact_information': project_id.contact_information,
                'cost_price': project_id.cost_price,
                'buffer': project_id.buffer,
            },
            "success": True,
            "status_code": 200,
            "message": "Success Create Project"
        })

    @http.route("/api/edit/project/engineering", auth="public", type="http", methods=["POST"], csrf=False)
    def EditProjectEngineering(self, **post):
        project = post.get('project_id')
        name = post.get('name', '').title()
        street = post.get('street', '').title()
        street2 = post.get('street2', '').title()
        city = post.get('city', '').title()
        state_id = post.get('state_id')
        zip = post.get('zip')
        customer = post.get('customer')
        poc_name = post.get('poc_name', '').title()
        contact_information = post.get('contact_information')
        cost_price = post.get('cost_price')
        buffer = post.get('buffer')

        if not project:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "The Project ID Is Null."
            })
        else:
            project_id = request.env['project.interior'].sudo().search([('id', '=', project)])
            if project_id:
                if state_id and customer:
                    state = request.env['res.country.state'].sudo().search([('id', '=', state_id)])
                    customer_id = request.env['res.customer'].sudo().search([('id', '=', customer)])
                    project_id.write({
                        'name': name if name else project_id.name,
                        'street': street if street else project_id.street,
                        'street2': street2 if street2 else project_id.street2,
                        'city': city if city else project_id.city,
                        'state_id': state.id if state.id else project_id.state_id.id,
                        'zip': zip if zip else project_id.zip,
                        'customer_id': customer_id.id if customer_id.id else project_id.customer_id.id,
                        'poc_name': poc_name if poc_name else project_id.poc_name,
                        'contact_information': contact_information if contact_information else project_id.contact_information,
                        'cost_price': cost_price if cost_price else project_id.cost_price,
                        'buffer': buffer if buffer else project_id.buffer
                    })
                elif state_id:
                    state = request.env['res.country.state'].sudo().search([('id', '=', state_id)])
                    project_id.write({
                        'name': name if name else project_id.name,
                        'street': street if street else project_id.street,
                        'street2': street2 if street2 else project_id.street2,
                        'city': city if city else project_id.city,
                        'state_id': state.id if state.id else project_id.state_id.id,
                        'zip': zip if zip else project_id.zip,
                        'poc_name': poc_name if poc_name else project_id.poc_name,
                        'contact_information': contact_information if contact_information else project_id.contact_information,
                        'cost_price': cost_price if cost_price else project_id.cost_price,
                        'buffer': buffer if buffer else project_id.buffer
                    })
                elif customer:
                    customer_id = request.env['res.customer'].sudo().search([('id', '=', customer)])
                    project_id.write({
                        'name': name if name else project_id.name,
                        'street': street if street else project_id.street,
                        'street2': street2 if street2 else project_id.street2,
                        'city': city if city else project_id.city,
                        'zip': zip if zip else project_id.zip,
                        'customer_id': customer_id.id if customer_id.id else project_id.customer_id.id,
                        'poc_name': poc_name if poc_name else project_id.poc_name,
                        'contact_information': contact_information if contact_information else project_id.contact_information,
                        'cost_price': cost_price if cost_price else project_id.cost_price,
                        'buffer': buffer if buffer else project_id.buffer
                    })
                else:
                    project_id.write({
                        'name': name if name else project_id.name,
                        'street': street if street else project_id.street,
                        'street2': street2 if street2 else project_id.street2,
                        'city': city if city else project_id.city,
                        'zip': zip if zip else project_id.zip,
                        'poc_name': poc_name if poc_name else project_id.poc_name,
                        'contact_information': contact_information if contact_information else project_id.contact_information,
                        'cost_price': cost_price if cost_price else project_id.cost_price,
                        'buffer': buffer if buffer else project_id.buffer
                    })
                return json.dumps({
                    "data": {
                        'id': project_id.id,
                    },
                    "success": True,
                    "status_code": 200,
                    "message": f"Success Edit {project_id.id}"
                })
            else:
                return json.dumps({
                    "success": False,
                    "status_code": 409,
                    "message": "The Project ID Not Exist."
                })

    @http.route('/api/edit/customer', auth="public", type="http", methods=["POST"], csrf=False)
    def EditCustomer(self, **post):
        customer_id = post.get('customer_id')
        name = post.get('name', '').title()
        street = post.get('street', '').title()
        street2 = post.get('street2', '').title()
        city = post.get('city', '').title()
        state_id = post.get('state_id')
        zip = post.get('zip')
        phone = post.get('phone')
        mobile = post.get('mobile')
        email = post.get('email')
        image_1998 = post.get('image_1998')
        tag_id = post.get('tag_id')

        if not customer_id:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "The Customer ID Is Null."
            })
        else:
            customer = request.env['res.customer'].sudo().search([('id', '=', customer_id)])
            if customer:
                if image_1998 and state_id:
                    state = request.env['res.country.state'].sudo().search([('id', '=', state_id)])
                    content = image_1998.read()
                    base64e = base64.b64encode(content)
                    customer.write({
                        'name': name if name else customer.name,
                        'street': street if street else customer.street,
                        'street2': street2 if street2 else False,
                        'city': city if city else customer.city,
                        'zip': zip if zip else customer.zip,
                        'phone': phone if phone else customer.phone,
                        'mobile': mobile if mobile else customer.mobile,
                        'email': email if email else customer.email,
                        'tag_id': tag_id if tag_id else customer.tag_id,
                        'state_id': state.id if state.id else customer.state_id.id,
                        'image_1998': base64e if base64e else customer.image_1998
                    })
                elif state_id:
                    state = request.env['res.country.state'].sudo().search([('id', '=', state_id)])
                    customer.write({
                        'name': name if name else customer.name,
                        'street': street if street else customer.street,
                        'street2': street2 if street2 else False,
                        'city': city if city else customer.city,
                        'zip': zip if zip else customer.zip,
                        'phone': phone if phone else customer.phone,
                        'mobile': mobile if mobile else customer.mobile,
                        'email': email if email else customer.email,
                        'tag_id': tag_id if tag_id else customer.tag_id,
                        'state_id': state.id if state.id else customer.state_id.id,
                    })
                elif image_1998:
                    content = image_1998.read()
                    base64e = base64.b64encode(content)
                    customer.write({
                        'name': name if name else customer.name,
                        'street': street if street else customer.street,
                        'street2': street2 if street2 else False,
                        'city': city if city else customer.city,
                        'zip': zip if zip else customer.zip,
                        'phone': phone if phone else customer.phone,
                        'mobile': mobile if mobile else customer.mobile,
                        'email': email if email else customer.email,
                        'tag_id': tag_id if tag_id else customer.tag_id,
                        'image_1998': base64e if base64e else customer.image_1998
                    })
                else:
                    customer.write({
                        'name': name if name else customer.name,
                        'street': street if street else customer.street,
                        'street2': street2 if street2 else False,
                        'city': city if city else customer.city,
                        'zip': zip if zip else customer.zip,
                        'phone': phone if phone else customer.phone,
                        'mobile': mobile if mobile else customer.mobile,
                        'email': email if email else customer.email,
                        'tag_id': tag_id if tag_id else customer.tag_id,
                    })
                return json.dumps({
                    "data": {
                        'id': customer.id,
                    },
                    "success": True,
                    "status_code": 200,
                    "message": f"Success Edit {customer.id}"
                })
            else:
                return json.dumps({
                    "success": False,
                    "status_code": 409,
                    "message": "The Customer ID Not Exist."
                })

    @http.route('/api/edit/agency', auth="public", type="http", methods=["POST"], csrf=False)
    def EditAgency(self, **post):
        agency_id = post.get('agency_id')
        name = post.get('name', '').title()
        street = post.get('street', '').title()
        street2 = post.get('street2', '').title()
        city = post.get('city', '').title()
        poc_name = post.get('poc_name', '').title()
        gst_required = post.get('gst_required')
        gst_no = post.get('gst_no')
        state_id = post.get('state_id')
        zip = post.get('zip')
        phone = post.get('phone')
        mobile = post.get('mobile')
        email = post.get('email')
        image_1998 = post.get('image_1998')
        tag_id = post.get('tag_id')

        if not agency_id:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "The Agency ID Is Null."
            })
        else:
            agency = request.env['res.agency'].sudo().search([('id', '=', agency_id)])
            if agency:
                if image_1998 and state_id:
                    state = request.env['res.country.state'].sudo().search([('id', '=', state_id)])
                    content = image_1998.read()
                    base64e = base64.b64encode(content)
                    agency.write({
                        'name': name if name else agency.name,
                        'street': street if street else agency.street,
                        'street2': street2 if street2 else False,
                        'city': city if city else agency.city,
                        'zip': zip if zip else agency.zip,
                        'phone': phone if phone else agency.phone,
                        'mobile': mobile if mobile else agency.mobile,
                        'email': email if email else agency.email,
                        'poc_name': poc_name if poc_name else agency.poc_name,
                        'gst_required': gst_required if gst_required else agency.gst_required,
                        'gst_no': gst_no if gst_no else agency.gst_no,
                        'tag_id': tag_id if tag_id else agency.tag_id,
                        'state_id': state.id if state.id else agency.state_id.id,
                        'image_1998': base64e if base64e else agency.image_1998
                    })
                elif state_id:
                    state = request.env['res.country.state'].sudo().search([('id', '=', state_id)])
                    agency.write({
                        'name': name if name else agency.name,
                        'street': street if street else agency.street,
                        'street2': street2 if street2 else False,
                        'city': city if city else agency.city,
                        'zip': zip if zip else agency.zip,
                        'phone': phone if phone else agency.phone,
                        'mobile': mobile if mobile else agency.mobile,
                        'email': email if email else agency.email,
                        'poc_name': poc_name if poc_name else agency.poc_name,
                        'gst_required': gst_required if gst_required else agency.gst_required,
                        'gst_no': gst_no if gst_no else agency.gst_no,
                        'tag_id': tag_id if tag_id else agency.tag_id,
                        'state_id': state.id if state.id else agency.state_id.id,
                    })
                elif image_1998:
                    content = image_1998.read()
                    base64e = base64.b64encode(content)
                    agency.write({
                        'name': name if name else agency.name,
                        'street': street if street else agency.street,
                        'street2': street2 if street2 else False,
                        'city': city if city else agency.city,
                        'zip': zip if zip else agency.zip,
                        'phone': phone if phone else agency.phone,
                        'mobile': mobile if mobile else agency.mobile,
                        'email': email if email else agency.email,
                        'poc_name': poc_name if poc_name else agency.poc_name,
                        'gst_required': gst_required if gst_required else agency.gst_required,
                        'gst_no': gst_no if gst_no else agency.gst_no,
                        'tag_id': tag_id if tag_id else agency.tag_id,
                        'image_1998': base64e if base64e else agency.image_1998
                    })
                else:
                    agency.write({
                        'name': name if name else agency.name,
                        'street': street if street else agency.street,
                        'street2': street2 if street2 else False,
                        'city': city if city else agency.city,
                        'zip': zip if zip else agency.zip,
                        'phone': phone if phone else agency.phone,
                        'mobile': mobile if mobile else agency.mobile,
                        'email': email if email else agency.email,
                        'poc_name': poc_name if poc_name else agency.poc_name,
                        'gst_required': gst_required if gst_required else agency.gst_required,
                        'gst_no': gst_no if gst_no else agency.gst_no,
                        'tag_id': tag_id if tag_id else agency.tag_id,
                    })
                return json.dumps({
                    "data": {
                        'id': agency.id,
                    },
                    "success": True,
                    "status_code": 200,
                    "message": f"Success Edit {agency.id}"
                })
            else:
                return json.dumps({
                    "success": False,
                    "status_code": 409,
                    "message": "The Agency ID Not Exist."
                })

    @http.route('/api/edit/receivable', auth="public", type="http", methods=["POST"], csrf=False)
    def EditReceivable(self, **post):
        receivable_id = post.get('receivable_id')
        payment_method = post.get('payment_method')
        sale_invoice = post.get('sale_invoice')
        payment_date = post.get('payment_date')
        customer_payment = post.get('customer_payment')

        if not receivable_id:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "The Receivable ID Is Null."
            })
        elif receivable_id:
            receivable = request.env['payment.method'].sudo().search([('id', '=', receivable_id)])
            if receivable:
                receivable.write({
                    'payment_method': payment_method if payment_method else receivable.payment_method,
                    'payment_date': payment_date if payment_date else receivable.payment_date,
                    'customer_payment': customer_payment if customer_payment else receivable.customer_payment,
                    'sale_invoice': sale_invoice if sale_invoice else receivable.sale_invoice
                })
            return json.dumps({
                "data": {
                    'id': receivable.id,
                },
                "success": True,
                "status_code": 200,
                "message": f"Success Edit {receivable.id}"
            })
        else:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "The Receivable ID Not Exist."
            })

    @http.route('/api/edit/expenses', auth="public", type="http", methods=["POST"], csrf=False)
    def EditExpenses(self, **post):
        expenses_id = post.get('expenses_id')
        if not expenses_id:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "The Expenses ID Is Null."
            })
        # Search expense record
        expenses = request.env['project.expenses'].sudo().search([('id', '=', expenses_id)])
        if not expenses:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "The Expenses ID Does Not Exist."
            })

        # Prepare values
        vals = {}
        name = post.get('name')
        if name:
            vals['name'] = name

        project = post.get('project_id')
        if project:
            project_id = request.env['project.interior'].sudo().search([('id', '=', int(project))], limit=1)
            if project_id:
                vals['project_id'] = project_id.id

        expenses_category = post.get('category_id')
        if expenses_category:
            category_id = request.env['expenses.category'].sudo().search([('id', '=', int(expenses_category))], limit=1)
            if category_id:
                vals['category_id'] = category_id.id

        agency = post.get('agency_id')
        if agency:
            agency_id = request.env['res.agency'].sudo().search([('id', '=', int(agency))], limit=1)
            if agency_id:
                vals['agency_id'] = agency_id.id

        agency_category = post.get('agency_category')
        if agency_category:
            agency_category_id = request.env['agency.category'].sudo().search([('id', '=', int(agency_category))],
                                                                              limit=1)
            if agency_category_id:
                vals['agency_category'] = agency_category_id.id

        paid_by_employee = post.get('paid_by_employee_id')
        if paid_by_employee:
            paid_by_employee_id = request.env['res.users'].sudo().search([('id', '=', int(paid_by_employee))], limit=1)
            if paid_by_employee_id:
                vals['paid_by_employee_id'] = paid_by_employee_id.id

        is_person = post.get('is_person')
        if is_person is not None:
            vals['is_person'] = is_person

        person_name = post.get('person_name')
        if person_name:
            vals['person_name'] = person_name

        expense_date = post.get('expense_date')
        if expense_date:
            vals['expense_date'] = expense_date

        total_amount = post.get('total_amount')
        if total_amount:
            vals['total_amount'] = total_amount

        payment_type = post.get('payment_type')
        if payment_type:
            vals['payment_type'] = payment_type

        remark = post.get('remark')
        if remark:
            vals['remark'] = remark

        # Write to the record
        if vals:
            expenses.write(vals)
            return json.dumps({
                "data": {
                    'id': expenses.id,
                },
                "success": True,
                "status_code": 200,
                "message": f"Success Edit {expenses.id}"
            })
        else:
            return json.dumps({
                "success": False,
                "status_code": 400,
                "message": "No valid fields provided to update."
            })

    @http.route("/api/project/quotation", auth="public", type="http", methods=["POST"], csrf=False)
    def CreateProjectQuotation(self, **post):
        project = post.get('project_id')
        agency_category = post.get('agency_category_id')
        buffer = post.get('buffer')
        amount = post.get('amount')
        vendor_id = post.get('vendor_id')
        agency = request.env['res.agency'].sudo().search([('id', '=', vendor_id)])
        project_id = request.env['project.interior'].sudo().search([('id', '=', project)])
        agency_work_id = request.env['agency.category'].sudo().search([('id', '=', agency_category)])
        if not agency_category:
            return json.dumps({
                "success": False,
                "status_code": 409,
                "message": "Not Create Quotation"
            })
        else:
            quotation_id = request.env['res.quotation'].sudo().create({
                'interior_project_id': project_id.id,
                'agency_category': agency_work_id.id,
                'buffer': project_id.buffer,
                'amount': amount,
                'vendor_id': agency.id
            })
            return json.dumps({
                "data": {
                    "id": quotation_id.id
                },
                "success": True,
                "status_code": 200,
                "message": "Success Create Quotation"
            })

    @http.route('/api/report/project', type='http', auth='public', methods=['POST'], csrf=False)
    def report_project_pdf(self, **post):
        raw_project_ids = post.get('project_ids', [])
        start_date = post.get('start_date')
        end_date = post.get('end_date')
        if not start_date or not end_date:
            return {
                "success": False,
                "status_code": 409,
                "message": "start_date and end_date are required."
            }
        project_ids = []
        if isinstance(raw_project_ids, str) and raw_project_ids.strip():
            try:
                project_ids = ast.literal_eval(raw_project_ids.strip())
            except Exception:
                return {
                    "success": False,
                    "status_code": 409,
                    "message": "Invalid format for project_ids. Expected a list of integers.",
                }
        elif isinstance(raw_project_ids, list):
            project_ids = raw_project_ids

        if project_ids and (not isinstance(project_ids, list) or not all(isinstance(i, int) for i in project_ids)):
            return {
                "success": False,
                "status_code": 400,
                "message": "project_ids must be a list of integers.",
            }

        domain = [
            ('create_date', '>=', start_date),
            ('create_date', '<=', end_date),
        ]
        if project_ids:
            domain.append(('id', 'in', project_ids))

        print("Domain:", domain)

        projects = request.env['project.interior'].sudo().search(domain)
        print("Projects found:", projects)

        if not projects:
            return {
                "success": False,
                "status_code": 404,
                "message": "No projects found in the given date range."
            }

        all_project_data = []
        for project in projects:
            project_data = request.env['project.report'].sudo()._generate_data_mobile(start_date, end_date, project.id)
            if project_data:
                all_project_data.extend(project_data)

        company_logo = base64.b64encode(request.env.company.logo or b'').decode('utf-8')
        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'saara_spaces_models.project_report_action_template',
            data={
                'data': all_project_data,
                'start_date': start_date,
                'end_date': end_date,
                'company_logo': company_logo,
            }
        )

        encoded_project_pdf = base64.b64encode(pdf_content).decode('utf-8')
        return request.make_response(
            json.dumps({
                "success": True,
                "status_code": 200,
                "filename": f"project_report_{start_date}_to_{end_date}.pdf",
                "pdf_base64": encoded_project_pdf,
            }),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/api/report/agency', type='http', auth='public', methods=['POST'], csrf=False)
    def report_agency_pdf(self, **post):
        raw_agency_ids = post.get('agency_ids', [])
        start_date = post.get('start_date')
        end_date = post.get('end_date')
        if not start_date or not end_date:
            return {
                "success": False,
                "status_code": 409,
                "message": "start_date and end_date are required."
            }
        agency_ids = []
        if isinstance(raw_agency_ids, str) and raw_agency_ids.strip():
            try:
                agency_ids = ast.literal_eval(raw_agency_ids.strip())
            except Exception:
                return {
                    "success": False,
                    "status_code": 409,
                    "message": "Invalid format for project_ids. Expected a list of integers.",
                }
        elif isinstance(raw_agency_ids, list):
            agency_ids = raw_agency_ids

        if agency_ids and (not isinstance(agency_ids, list) or not all(isinstance(i, int) for i in agency_ids)):
            return {
                "success": False,
                "status_code": 400,
                "message": "project_ids must be a list of integers.",
            }
        domain = [
            ('create_date', '>=', start_date),
            ('create_date', '<=', end_date),
        ]
        if agency_ids:
            domain.append(('id', 'in', agency_ids))
        agecnys = request.env['res.agency'].sudo().search(domain)
        print("Projects found:", agecnys)
        if not agecnys:
            return {
                "success": False,
                "status_code": 404,
                "message": "No projects found in the given date range."
            }
        all_agency_data = []
        company_logo = base64.b64encode(request.env.company.logo or b'').decode('utf-8')
        currency_id = request.env.company.currency_id.symbol
        for agency in agecnys:
            agency_data = request.env['agency.report'].sudo()._generate_data_mobile(start_date, end_date, agency.id)
            grouped_by_project = request.env['agency.report'].sudo()._group_by_project(agency_data['report_data'])
            if agency_data:
                all_agency_data.append({
                    'agency_ids': agency.name,
                    'currency_id': currency_id,
                    'project_groups': grouped_by_project,  # <-- grouped result here
                    'TOTAL_paid': agency_data['total_expense_sum'] + agency_data['total_vendor_sum'],
                    'total_cash_payment': agency_data['total_cash_payment'],
                    'total_bank_payment': agency_data['total_bank_payment'],
                    'TOTAL_CTC': agency_data['TOTAL_CTC'],
                    'TOTAL_remaining': agency_data['TOTAL_CTC'] - (
                            agency_data['total_expense_sum'] + agency_data['total_vendor_sum']),
                    'report_data': agency_data  # Embed the report inside
                })
        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'saara_spaces_models.agency_report_action_template_new',
            data={
                'data': all_agency_data,
                'start_date': start_date,
                'end_date': end_date,
                'company_logo': company_logo,
            }
        )
        encoded_agency_pdf = base64.b64encode(pdf_content).decode('utf-8')
        # headers = [
        #     ('Content-Type', 'application/pdf'),
        #     ('Content-Disposition', f'attachment; filename="agency_report{start_date}_to_{end_date}.pdf"'),
        # ]
        return request.make_response(
            json.dumps({
                "success": True,
                "status_code": 200,
                "filename": f"agency_report_{start_date}_to_{end_date}.pdf",
                "pdf_base64": encoded_agency_pdf,
            }),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/api/report/month/account', type='http', auth='public', methods=['POST'], csrf=False)
    def report_month_account_pdf(self, **post):
        start_date = post.get('start_date')
        end_date = post.get('end_date')
        if not start_date or not end_date:
            return {
                "success": False,
                "status_code": 409,
                "message": "start_date and end_date are required."
            }

        domain = [
            ('create_date', '>=', start_date),
            ('create_date', '<=', end_date),
        ]

        work_data = request.env['work.category.report'].sudo()._generate_data_agency_mobile(start_date, end_date)
        report_data = work_data.get('report_data', [])
        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'saara_spaces_models.work_category_report_action_template',
            data={
                'data': report_data,
                'start_date': start_date,
                'end_date': end_date,
            }
        )
        encoded_account_pdf = base64.b64encode(pdf_content).decode('utf-8')
        # headers = [
        #     ('Content-Type', 'application/pdf'),
        #     ('Content-Disposition', f'attachment; filename="agency_report{start_date}_to_{end_date}.pdf"'),
        # ]
        # return request.make_response(pdf_content, headers)
        return request.make_response(
            json.dumps({
                "success": True,
                "status_code": 200,
                "filename": f"agency_report_{start_date}_to_{end_date}.pdf",
                "pdf_base64": encoded_account_pdf,
            }),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/project/expenses/chart/data', type='json', auth='user')
    def get_expense_data(self):
        data = request.env['project.expenses'].get_expense_chart_data()
        return data

    @http.route('/cash/flow/chart/data', type='json', auth='user')
    def get_cash_flow_data(self):
        # Default dicts to accumulate by year
        credit_by_year = defaultdict(float)
        debit_by_year = defaultdict(float)

        # Get all customer payments (credits)
        credit_records = request.env['payment.method'].search([])
        for record in credit_records:
            if record.payment_date:
                year = record.payment_date.year
                credit_by_year[year] += record.customer_payment

        # Get all vendor payments (debits)
        debit_records = request.env['vendor.payment.method'].search([])
        for record in debit_records:
            if record.payment_date:
                year = record.payment_date.year
                debit_by_year[year] += record.total_payment

        # Collect unique years and sort
        all_years = sorted(set(credit_by_year.keys()) | set(debit_by_year.keys()))

        # Prepare data for chart
        data = {
            'labels': [str(year) for year in all_years],
            'credits': [credit_by_year[year] for year in all_years],
            'debits': [debit_by_year[year] for year in all_years],
        }
        return data

    @http.route('/project/cost/chart/data', type='json', auth='user')
    def project_cost_chart_data(self):
        records = request.env['project.interior'].search([])
        result = []

        for rec in records:
            result.append({
                'name': rec.name,
                'revenue': rec.customer_amount,
                'expense': rec.total_expenses_amount,
            })
        return result

    @http.route('/agency/payment/count/chart/data', type='json', auth='user')
    def get_agency_expense_and_payment_data(self):
        vendor_data = defaultdict(lambda: {
            'name': '',
            'total_expense': 0.0,
            'total_payment': 0.0,
            'projects': set(),
        })

        # Fetch Vendor Payments
        payment_records = request.env['vendor.payment.method'].search([])
        for rec in payment_records:
            vendor_id = rec.vendor_id.id
            vendor_data[vendor_id]['name'] = rec.vendor_id.name
            vendor_data[vendor_id]['total_payment'] += rec.vendor_payment
            if rec.interior_project_id:
                vendor_data[vendor_id]['projects'].add(rec.interior_project_id.name)

        # Fetch Expenses
        expense_records = request.env['project.expenses'].search([])
        for exp in expense_records:
            vendor_id = exp.agency_id.id
            if vendor_id:  # only if linked to a vendor
                vendor_data[vendor_id]['name'] = exp.agency_id.name
                vendor_data[vendor_id]['total_expense'] += exp.total_amount
                if exp.project_id:
                    vendor_data[vendor_id]['projects'].add(exp.project_id.name)

        # Format Result
        result = []
        for data in vendor_data.values():
            if data['name']:
                result.append({
                    'name': data['name'],
                    'projects': ', '.join(data['projects']),
                    'total_expense': data['total_expense'],
                    'total_payment': data['total_payment'],
                })
        return result
