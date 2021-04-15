# -*- coding: utf-8 -*-

from odoo import models, fields, api


class mc_aboutcompany(models.AbstractModel):
    _name = 'mc_aboutcompany'
    _description='aboutcompany'



class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_ir_module_module_data(self, domain):
        records = self.search(domain)
        result_dict = []
        translation_result = []
        current_user_lang = self.env['res.users'].search([['id', '=', self.env.uid]])['partner_id']['lang']

        for record in records:
            result_dict.append({
                'id': record['id'],
                'name': record['name'],
                'icon': record['icon'],
                'shortdesc': record['shortdesc'],
                'summary': record['summary'],
                'state': record['state'].capitalize(),
            })

        for record in result_dict:
            shortdesc = self._query_statement_ir_translation(record['id'], 'shortdesc', current_user_lang,
                                                             record['shortdesc'])

            summary = self._query_statement_ir_translation(record['id'], 'summary', current_user_lang,
                                                           record['summary'])

            state = self._query_statement_ir_translation('0', 'state', current_user_lang,record['state'])

            translation_result.append({
                'id': record['id'],
                'name': record['name'],
                'icon': record['icon'],
                'shortdesc': record['shortdesc'] if shortdesc == [] else shortdesc[0][0],
                'summary': record['summary'] if summary == [] else summary[0][0],
                'state': record['state'] if state == [] else state[0][0],

            })

        return translation_result

    def _query_statement_ir_translation(self, res_id, name, lang, src):

        field_name = '{}{}'.format('ir.module.module,', name)

        sql = """
            select value from ir_translation
            where res_id={} and name='{}' and lang='{}' and src='{}';
        """.format(res_id, field_name, lang, src)

        self.env.cr.execute(sql)

        return self.env.cr.fetchall()
