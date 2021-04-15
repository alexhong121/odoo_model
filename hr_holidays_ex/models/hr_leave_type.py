# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api

class HolidaysType(models.Model):
    _inherit='hr.leave.type'

    # def _default_validity_start_year(self):
    #     results=[]
    #     currentYear=int(datetime.datetime.strftime(fields.datetime.now(), '%Y'))
    #     for i in range(-1,9):
    #         tup=(str(currentYear+i),str(currentYear+i))
    #         results.append(tup)
    #     return results

    validity_interval_type=fields.Selection(
        selection=[
            ('hr_leave_allocation','依准假單指定'),
            ('due_date','依到職日年資計算')],
        string='准假時長',
        default='hr_leave_allocation',
        required=True
    )
    validity_type=fields.Selection(
        selection=[
            ('direct_setting','直接指定'),
            ('due_date','依到職日年資計算')
        ],
        default='direct_setting',
        required = True,
        readonly=False
    )
    validity_type_display=fields.Selection(
        selection=[
            ('direct_setting', '直接指定'),
            ('due_date', '依到職日年資計算')
        ],
        string='有效期間判定',
        store=False,
        readonly=True,
        compute='_compute_validity_type_display'
    )
    validity_start_year=fields.Selection(
        selection=[('2019','2019')],
        string="有效起始年份",
        default='2019',
        required = True
    )
    #########################
    #       UI method       #
    #########################
    @api.multi
    @api.onchange('validity_interval_type')
    @api.depends('validity_type')
    def _compute_validity_type_display(self):
        for leaveType in self:
            leaveType.validity_type_display=leaveType.validity_type

    ###############################
    #       Activity method       #
    ###############################
    @api.onchange('validity_interval_type')
    def _onchange_validity_interval_type(self):
        if self.validity_interval_type=='hr_leave_allocation':
            self.validity_type='direct_setting'
        elif self.validity_interval_type=='due_date':
            self.validity_type='due_date'

    #############################
    #   ORM Overrides methods   #
    #############################
    # override
    @api.multi
    def name_get(self):
        if not self._context.get('employee_id'):
            # leave counts is based on employee_id, would be inaccurate if not based on correct employee
            return super(HolidaysType, self).name_get()
        res = []
        for record in self:
            name = record.name
            res.append((record.id, name))
        return res