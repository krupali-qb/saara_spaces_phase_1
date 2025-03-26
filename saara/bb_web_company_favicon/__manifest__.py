# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Customize Company Backend web icon',
    'version': '17.0.0.1',
    'category': 'Extra Tools',
    'icon': '/bb_web_company_favicon/static/description/icon.png',
    'sequence': 20,
    'author': '',
    'summary': 'The custom web window Favicon',
    'description': """
        Customize Favicon
            """,
    'depends': ['web'],
    'data': [
        'views/res_company.xml',
    ],
    'installable': True,
    'auto_install': False,
    "application": True,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'bb_web_company_favicon/static/src/js/favicon.js',
        ],
    },
    'qweb': [

    ],
}
