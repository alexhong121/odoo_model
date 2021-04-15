# -*- coding: utf-8 -*-
from odoo import http

class Backend(http.Controller):
    @http.route('/backend/backend/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    # @http.route('/backend/backend/objects/', auth='public')
    # def list(self, **kw):
    #     return http.request.render('backend.listing', {
    #         'root': '/backend/backend',
    #         'objects': http.request.env['backend.backend'].search([]),
    #     })
    #
    # @http.route('/backend/backend/objects/<model("backend.backend"):obj>/', auth='public')
    # def object(self, obj, **kw):
    #     return http.request.render('backend.object', {
    #         'object': obj
    #     })