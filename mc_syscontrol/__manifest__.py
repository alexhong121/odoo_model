# -*- coding: utf-8 -*-
{
    'name': "backend",

    'summary': """
        修改界面""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mail','hr','web','base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/hr_groups.xml',
        'views/assets.xml',
        'views/views.xml',
        'views/res_company_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        'static/src/xml/base.xml',
        'static/src/xml/dashboard.xml',
        'static/src/xml/systray.xml',
    ],
}