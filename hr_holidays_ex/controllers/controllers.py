# -*- coding: utf-8 -*-
from odoo import http

# class HrHolidaysExtend(http.Controller):
#     @http.route('/hr_holidays_extend/hr_holidays_extend/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_holidays_extend/hr_holidays_extend/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_holidays_extend.listing', {
#             'root': '/hr_holidays_extend/hr_holidays_extend',
#             'objects': http.request.env['hr_holidays_extend.hr_holidays_extend'].search([]),
#         })

#     @http.route('/hr_holidays_extend/hr_holidays_extend/objects/<model("hr_holidays_extend.hr_holidays_extend"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_holidays_extend.object', {
#             'object': obj
#         })