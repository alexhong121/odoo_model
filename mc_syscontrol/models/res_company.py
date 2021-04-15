# -*- coding: utf-8 -*-

from odoo import models, fields, api



class ResCompany(models.Model):
    """
    增加 公司設定 "abbreviation""en_name""en_abbreviation" field
    """
    _inherit = 'res.company'

    abbreviation=fields.Char(string="簡稱",defaulf="Mc")
    en_name=fields.Char(string="英文名稱")
    en_abbreviation=fields.Char(string="英文簡稱")


