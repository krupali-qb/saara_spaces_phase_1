{
    'name': 'Multi Level Leave Policy',
    'version': '1.1',
    'category': 'Human Resources',
    'summary': 'Leave Types and Approval Policy Management',
    'author': 'Custom',
    'depends': ['hr_holidays', 'hr',],
    'data': [
        #'security/ir.model.access.csv',
        #'data/leave_types.xml',
        'data/ir_cron_data.xml',
        #'views/hr_leave_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
