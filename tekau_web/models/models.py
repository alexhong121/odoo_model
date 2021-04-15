# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Factory(models.Model):
    # 3/25 建立表格欄位 圖片 名子 說明
    _name = 'tekau_factory'

    name = fields.Char(string='標題')
    description= fields.Text(string='說明')
    image=fields.Binary(string='圖片')
    image_filename = fields.Char("Image Filename")

    # value = fields.Integer()
    # value2 = fields.Float(compute="_value_pc", store=True)
    # description = fields.Text()

    @api.depends('value')
    def _value_pc(self):
        # self.value2 = float(self.value) / 100
        pass