# -*- coding: utf-8 -*-
{
    'name': "hr_holidays_extend",

    'summary': """
        hr_holidays extend functions
    """,

    'description': """
        Long description of module's purpose
    """,

    'author': "MC",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_holidays'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_leave_type_views.xml',
        'views/hr_leave_allocation_views.xml',
        'views/hr_leave_views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}