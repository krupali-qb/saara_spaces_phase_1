{
    "name": "Employee LWP Dashboard",
    "version": "1.0",
    "depends": ["hr", "hr_holidays",'web'],
    "author": "Your Name",
    "category": "Human Resources",
    "description": "Dashboard showing LWP leave count for logged-in employee",
    "data": [
        "security/ir.model.access.csv",
        "views/dashboard_view.xml"
    ],
    'assets': {
        'web.assets_backend': [
            'employee_lwp_dashboard/static/src/js/lwp_dashboard.js',
            'employee_lwp_dashboard/static/src/xml/lwp_dashboard_template.xml',
        ],
    },
    "installable": True,
    "application": True
}
