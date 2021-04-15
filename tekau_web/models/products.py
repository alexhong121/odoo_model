# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Product(models.Model):
    # 3/25 建立表格欄位 圖片 名子 說明
    _name = 'tekau_products'

    name = fields.Char(string='產品品名')
    description= fields.Text(string='說明')
    image=fields.Binary(string='產品圖片')
    image_filename = fields.Char("Image Filename")
    dimensions=fields.Binary(string='stl檔案')
    value = fields.Integer(string='該類別的總數量')
    type=fields.Char(string='類型')
    # value2 = fields.Float(compute="_value_pc", store=True)
    # description = fields.Text()

    @api.depends('value')
    def _value_pc(self):
        # self.value2 = float(self.value) / 100
        pass