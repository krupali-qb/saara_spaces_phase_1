{
    'name': 'Multi Level Leave Policy',
    'version': '1.2',
    'category': 'Human Resources',
    'summary': 'Leave Types and Approval Policy Management',
    'author': 'Custom',
    'depends': ['hr_holidays', 'hr', ],
    'data': [
        # 'security/ir.model.access.csv',
        # 'data/leave_types.xml',
        'data/ir_cron_data.xml',
        'views/hr_leave_views.xml',
        'wizard/same_day.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'multi_level_leave_policy/static/src/js/hour_policy_leave.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
