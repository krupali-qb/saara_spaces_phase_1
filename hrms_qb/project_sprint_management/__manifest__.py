# -*- coding: utf-8 -*-
{
    'name': 'Project Sprint Management',
    'version': '1.0',
    'category': 'Project',
    'depends': ['project', 'web','calendar'],
    'data': [
        'security/ir.model.access.csv',

        'views/project_expense_view.xml',
        'views/project_views.xml',
        'wizard/start_sprint_wizard_views.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'project_sprint_management/static/src/js/custom_start_button.js',
            'project_sprint_management/static/src/xml/custom_start_button.xml',
        ],
    },
    'application': True,
}
