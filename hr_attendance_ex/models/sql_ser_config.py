# -*- coding: utf-8 -*-
import logging
# import pyodbc

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, MissingError

_logger = logging.getLogger(__name__)


class SQLConfig(models.Model):
    _name = 'sql.config'
    _description='sql_config'
    _sql_constraints = [('check_syncing', 'UNIQUE(syncing)', '資料庫同步只能設定一台')]

    name=fields.Char(string='名稱',required=True)
    server = fields.Char(string='伺服器')
    port = fields.Char(string='連接阜')
    database = fields.Char(string='資料庫')
    username = fields.Char(string='使用者名稱')
    password = fields.Char(string='密碼')
    odbc = fields.Selection([
        ('{ODBC Driver 17 for SQL Server}', 'ODBC Driver 17 for SQL Server')],
        string='ODBC 驅動程式',
        default='{ODBC Driver 17 for SQL Server}',
        required=True
    )
    syncing=fields.Boolean(string='同步中')


    @api.multi
    def test_connection(self):

        sql = self.sql_server_connection(
            odbc=self.odbc, server=self.server, port=self.port, database=self.database, username=self.username,
            password=self.password
        )
        #連線失敗時
        if not sql['sqlstate']:
            raise UserError(_(cursor['msg']))
        # 連線成功時
        if sql['sqlstate']:
            raise UserError(_("Connection Test Succeeded!"))

    def sql_server_connection(self, **kwargs):
        try:
            info = 'DRIVER={0}; SERVER={1},{2}; DATABASE={3}; UID={4}; PWD={5}'.format(
                kwargs['odbc'], kwargs['server'], kwargs['port'], kwargs['database'], kwargs['username'],
                kwargs['password']
            )
            sql = pyodbc.connect(info)
            return {'sqlstate':True,'sql':sql,'msg':None}
        except pyodbc.Error as err:
            sqlmsg = err.args[1]
            _logger.error(sqlmsg)
            return {'sqlstate':False,'sql':None,'msg':sqlmsg}


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.multi
    def sql_ser_config(self):
        self.ensure_one()
        template_form = self.env.ref('hr_attendance_extend.SQL_ser_config_form_themes')
        template_list = self.env.ref('hr_attendance_extend.SQL_ser_config_list_themes')

        return {
            'name': _('Choose'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sql.config',
            'views': [(template_list.id,'list'),(template_form.id, 'form')],
            'target': 'current',
        }
