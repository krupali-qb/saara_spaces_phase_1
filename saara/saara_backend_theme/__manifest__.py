# -*- coding: utf-8 -*-
{
    'name': 'Custom Backend Theme Saara spaces',
    'version': '17.0.1.0.0',
    'category': 'Theme',
    'summary': "Custom Backend Theme QB",
    'description': "Custom Backend Theme QB",
    'author': 'quantumbot',
    'company': 'quantumbot',
    'maintainer': 'quantumbot',
    'website': "https://quantumbot.in/",
    'depends': ['base'],
    'data': [
        # 'security/security.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 2,
    'assets': {
        'web.assets_backend': [
            'saara_backend_theme/static/src/scss/theme.scss',
        ],
        'web.assets_frontend': [
            'saara_backend_theme/static/src/scss/login_theme.scss',
        ],
    }
}
