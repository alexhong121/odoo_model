# -*- coding: utf-8 -*-
from odoo import http

# class McAboutconpany(http.Controller):
#     @http.route('/mc_aboutconpany/mc_aboutconpany/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mc_aboutconpany/mc_aboutconpany/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mc_aboutconpany.listing', {
#             'root': '/mc_aboutconpany/mc_aboutconpany',
#             'objects': http.request.env['mc_aboutconpany.mc_aboutconpany'].search([]),
#         })

#     @http.route('/mc_aboutconpany/mc_aboutconpany/objects/<model("mc_aboutconpany.mc_aboutconpany"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mc_aboutconpany.object', {
#             'object': obj
#         })