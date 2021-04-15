# -*- coding: utf-8 -*-

from odoo import models, fields, api


# 增加員工 "due_date"欄位
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def _sync_user(self, user):
        vals = dict(
            work_email=user.email,
        )
        if user.tz:
            vals['tz'] = user.tz
        return vals