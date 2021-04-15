# -*- coding: utf-8 -*-
import logging

from lxml import etree

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, MissingError

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _order = "create_date "

    check_in = fields.Datetime(string="Check In", required=False)
    work_type = fields.Selection(selection=[('overtime', 'Overtime'), ('normal', 'Normal')], default='normal',
                                 string='Shift')
    late_time = fields.Integer(string="Late(min)")
    leave_early_time = fields.Integer(string="Excused(min)")
    source = fields.Selection(selection=[('machine', 'Machine'),('relenishment','Relenishment')], string="Source")
    working_hours = fields.Integer(string="Working hours(min)")
    work_abnormal = fields.Selection(selection=[
        ('no check-in', 'No check-in'),
        ('no check-out', 'No check-out'),
        ('delay', 'Delay'),
        ('leave early', 'Leave early'),
        ('delay,leave early', 'Delay,Leave early'),
        ('delay,no check-out', 'Delay,No check-out'),
        ('no check-in,no check-out', 'No check-in,No check-out'),
        ('no check-in,leave early', 'No check-in,Leave early')
    ], string="Work abnormal", compute='_compute_worked_abnormal', store=True, readonly=True)
    check_in_issue = fields.Char(string="check_in_issue", store=True, readonly=True)
    check_out_issue = fields.Char(string="check_out_issue", store=True, readonly=True)
    relenishment_id = fields.Many2one('hr.replenishment', 'replenishment')
    check_date=fields.Date(string="打卡日期")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        ret_val = super().fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

        doc = etree.XML(ret_val['arch'])
        if view_type == 'form' and self.env.user.has_group('hr_attendance.group_hr_attendance_user'):
            for node_form in doc.xpath("//form"):
                node_form.set("edit", 'true')
        else:
            for node_form in doc.xpath("//form"):
                node_form.set("edit", 'false')
        ret_val['arch'] = etree.tostring(doc)
        return ret_val

    @api.multi
    def toggle_relenishment(self):
        template_form = self.env.ref('hr_attendance_extend.hr_replenishment_my_view_form')

        return {
            'name': _('relenishment'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.replenishment',
            'views': [(template_form.id, 'form')],
            'context': {
                'attendance_id': self.id,
                'default_user_id':self.env.uid,
            },
            'target': 'current',
        }

    @api.multi
    def name_get(self):
        result = []
        for attendance in self:
            if not attendance.check_out:
                result.append((attendance.id, _("%(empl_name)s from %(check_in)s") % {
                    'empl_name': attendance.employee_id.name,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance,
                                                                                            fields.Datetime.from_string(
                                                                                                attendance.check_in))),
                }))
            elif not attendance.check_in:
                result.append((attendance.id, _("%(empl_name)s from %(check_out)s") % {
                    'empl_name': attendance.employee_id.name,
                    'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance,
                                                                                             fields.Datetime.from_string(
                                                                                                 attendance.check_out))),
                }))
            else:
                result.append((attendance.id, _("%(empl_name)s from %(check_in)s to %(check_out)s") % {
                    'empl_name': attendance.employee_id.name,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance,
                                                                                            fields.Datetime.from_string(
                                                                                                attendance.check_in))),
                    'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance,
                                                                                             fields.Datetime.from_string(
                                                                                                 attendance.check_out))),
                }))
        return result

    @api.model_cr
    def init(self):
        pass

    @api.depends('check_in', 'check_out', 'late_time', 'leave_early_time')
    @api.multi
    def _compute_worked_abnormal(self):
        for attendance in self:
            textin = ""
            textout = ""
            if not attendance.check_in:
                attendance.write({
                    'check_in_issue': "no check-in"
                })
                # attendance.check_in_issue = "no check-in"
                textin = "no check-in"
            if attendance.check_in and attendance.late_time:
                attendance.write({
                    'check_in_issue': "delay"
                })
                textin = "delay"
            if not attendance.check_out:
                attendance.write({
                    'check_out_issue': "no check-out"
                })
                textout = "no check-out"
            if attendance.check_out and attendance.leave_early_time:
                attendance.write({
                    'check_out_issue': "leave early"
                })
                textout = "leave early"
            if textin.strip() == "":
                attendance.work_abnormal = textout
                # attendance.work_abnormal = textin + " , " + textout
            elif textout.strip() == "":
                attendance.work_abnormal = textin
            else:
                attendance.work_abnormal = textin + "," + textout

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                delta = attendance.check_out - attendance.check_in
                attendance.worked_hours = delta.total_seconds() / 3600.0

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        pass