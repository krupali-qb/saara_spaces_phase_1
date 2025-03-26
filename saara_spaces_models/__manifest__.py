# -*- coding: utf-8 -*-
{
    'name': 'interior project',
    'version': '17.0.3.0.2',
    'category': '',
    'summary': "",
    'author': 'quantumbot',
    'company': 'quantumbot',
    'maintainer': 'quantumbot',
    'website': "https://quantumbot.in/",
    'depends': ['web', 'base', 'mail','base_import','website'],
    'data': [
        'security/security_template.xml',
        'security/ir.model.access.csv',
        'views/interior_projects_view.xml',
        'views/payment_method_view.xml',
        'views/vendor_payment_method_view.xml',
        'views/res_customer_view.xml',
        'views/res_agency_view.xml',
        'views/menuitem_hide.xml',
        'views/expenses_category_view.xml',
        'views/agency_category_view.xml',
        'views/project_expense_view.xml',
        'views/weblogin_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'saara_spaces_models/static/src/**/*.xml',
        ],
    },

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 2,
}
