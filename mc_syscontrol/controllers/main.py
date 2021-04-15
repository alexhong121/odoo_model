# -*- coding: utf-8 -*-

from odoo import http
from odoo.addons.web.controllers.main import ReportController

#Overrider

class JsonRequest(http.JsonRequest):
    def _handle_exception(self, exception):
        """Called within an except block to allow converting exceptions
           to arbitrary responses. Anything returned (except None) will
           be used as response."""
        super(JsonRequest, self)._handle_exception(exception)
        print("HOIHI")

