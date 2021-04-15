# -*- coding: utf-8 -*-

from odoo import models, fields, api


# 增加員工 "due_date"欄位
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    due_date = fields.Date(string='到職日')


