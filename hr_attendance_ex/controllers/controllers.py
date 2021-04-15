# -*- coding: utf-8 -*-
import logging
from odoo import http

_logging = logging.getLogger(__name__)


class HrAttendaceExtend(http.Controller):
    @http.route('/hr_attendace_extend', methods=['GET', 'POST'], type='json',
                auth='public')
    def index(self, **kw):
        records = http.request.params.get('data')
        employee = http.request.env['hr.employee'].sudo()
        attendance = http.request.env['hr.attendance'].sudo()

        for recoord in records:
            if recoord['CHECKTYPE'] == 'I' and employee.search([('machine_id', '=', recoord['BADGENUMBER'])]).id:
                if attendance.search([('check_in', '=', recoord['CHECKTIME'])]):
                    _logging.error("正常班簽到　%s 已經存在,不得在新增紀錄" % (recoord['CHECKTIME']))
                attendance.create({
                    'check_in': recoord['CHECKTIME'],
                    'employee_id': employee.search([('machine_id', '=', recoord['BADGENUMBER'])]).id,
                    'work_type': 'normal'
                })
            if recoord['CHECKTYPE'] == 'O' and employee.search([('machine_id', '=', recoord['BADGENUMBER'])]).id:
                if attendance.search([('check_out', '=', recoord['CHECKTIME'])]):
                    _logging.error("正常班簽退　%s 已經存在,不得在新增紀錄" % (recoord['CHECKTIME']))
                att_one = attendance.search(
                    [('employee_id', '=', employee.search([('machine_id', '=', recoord['BADGENUMBER'])]).id),
                     ('check_out', '=', False), ('work_type', '=', 'normal')],
                    limit=1)
                att_one.write({'check_out': recoord['CHECKTIME']})

            if recoord['CHECKTYPE'] == 'i' and employee.search([('machine_id', '=', recoord['BADGENUMBER'])]).id:
                if attendance.search([('check_in', '=', recoord['CHECKTIME'])]):
                    _logging.error("加班簽到　%s 已經存在,不得在新增紀錄" % (recoord['CHECKTIME']))
                attendance.create({
                    'check_in': recoord['CHECKTIME'],
                    'employee_id': employee.search([('machine_id', '=', recoord['BADGENUMBER'])]).id,
                    'work_type': 'overtime'
                })
            if recoord['CHECKTYPE'] == 'o' and employee.search([('machine_id', '=', recoord['BADGENUMBER'])]).id:
                if attendance.search([('check_out', '=', recoord['CHECKTIME'])]):
                    _logging.error("加班簽退　%s 已經存在,不得在新增紀錄" % (recoord['CHECKTIME']))
                att_one = attendance.search(
                    [('employee_id', '=', employee.search([('machine_id', '=', recoord['BADGENUMBER'])]).id),
                     ('check_out', '=', False), ('work_type', '=', 'overtime')],
                    limit=1)
                att_one.write({'check_out': recoord['CHECKTIME']})

    @http.route('/hr_attendace_extend/config', auth='public', methods=['GET', 'POST'], type='json')
    def configuration(self,**kw ):
        data = http.request.params.get('data')
        sql_config=http.request.env['sql.config'].sudo()
        records=sql_config.search([('syncing','=',data['syncing'])])
        record_dict=[]
        for record in records:
            record_dict.append(
                {
                    'odbc': record['odbc'],
                    'server': record['server'],
                    'port': record['port'],
                    'database': record['database'],
                    'username': record['username'],
                    'password': record['password'],
                    'script':record['script'],
                }
            )
        return record_dict
    @http.route('/hr_attendace_extend/test/', auth='public')
    def configuration(self):
        sql_config=http.request.env['hr.attendance'].sudo()
        sql_config.create({
            'employee_id': "1",
            'check_in': "2019-10-02 10:38:42",
        })
        return 'hoho'