# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Contact(models.Model):
    # 3/25 建立表格欄位 圖片 名子 說明
    _name = 'tekau_contacts'

    name = fields.Char(string='姓名')
    content = fields.Text(string='內容')
    phone = fields.Char(string='電話號碼')
    email = fields.Char(string="電子郵件")

    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.user.company_id.id)
    partner_id = fields.Many2one('res.partner', string='Customer', track_visibility='onchange', track_sequence=1,
                                 index=True,
                                 help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")

    @api.model
    def create(self, values):
        contact_id = super().create(values)

        template = self.env.ref('tekau_web.new_customer_msg')

        self.env['mail.template'].browse(template.id).send_mail(contact_id.id, force_send=True, raise_exception=True)
        print(contact_id)
        return contact_id
