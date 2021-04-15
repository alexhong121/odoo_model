# -*- coding: utf-8 -*-
{
    'name': "hr_attendance_extend",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

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
    'depends': ['base', 'hr_attendance', 'hr'],

    # always loaded
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
        'views/SQL_ser_config_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_config_settings_templates.xml',
        'demo/vacation_days_data.xml',
        'views/hr_relenishment_views.xml',
        'security/security.xml',
        'Data/hr_attendance_mail_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        'static/src/xml/attendance.xml',
        'static/src/xml/vacations_days_comparison.xml',
        'static/src/xml/amap.xml',
        'static/src/xml/gmaps.xml',
        'static/src/xml/punch_time.xml',
    ]
}
