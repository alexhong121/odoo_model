# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class View(models.Model):
    _inherit = 'ir.ui.view'

    @api.model
    def render_template(self, template, values=None, engine='ir.qweb'):
        """
        重新 render template 帶入title value
        :param template:
        :param values:
        :param engine:
        :return:
        """
        if template in ['web.login', 'web.webclient_bootstrap']:
            if not values:
                values = {}
            # values["title"] = self.env['ir.config_parameter'].sudo().get_param("app_system_name", "MC")
            main_company=self.env['res.company']._get_main_company()
            values["title"]=main_company['abbreviation']
        return super(View, self).render_template(template, values=values, engine=engine)