import logging
from odoo import api, fields, models
import time
from datetime import datetime, date, time, timedelta
from pytz import timezone, UTC
from collections import namedtuple
from odoo.tools.translate import _
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

RelenAttendance = namedtuple('RelenAttendance', 'id,check_in, check_out, check_in_issue, check_out_issue, work_type')


class HrReplenishment(models.Model):
    _name = "hr.replenishment"
    _description = "Replenishment"
    _order = "date_punch desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'

    def _default_employee(self):
        # return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        attendance_id = self._context.get('attendance_id')
        if attendance_id:
            attendance = self.env['hr.attendance'].browse(attendance_id)
            # defaults.update(dict({
            #     'employee_id': attendance.employee_id.id,
            #     'attendance_id': attendance.id,
            #     'request_date_punch': attendance.create_date.date(),
            #     'yd': datetime(attendance.create_date.year, attendance.create_date.month, attendance.create_date.day, 0,
            #                    0, 0, 0).strftime("%Y-%m-%d %H:%M:%S"),
            #     'td': datetime(attendance.create_date.year, attendance.create_date.month, attendance.create_date.day,
            #                    23, 59, 59, 0).strftime("%Y-%m-%d %H:%M:%S"),
            # }))
            defaults.update(dict({
                'employee_id': attendance.employee_id.id,
                'attendance_id': attendance.id,
                'request_date_punch': attendance.check_date,
                'yd': datetime(attendance.check_date.year, attendance.check_date.month, attendance.check_date.day, 0,
                               0, 0, 0).strftime("%Y-%m-%d %H:%M:%S"),
                'td': datetime(attendance.check_date.year, attendance.check_date.month, attendance.check_date.day,
                               23, 59, 59, 0).strftime("%Y-%m-%d %H:%M:%S"),
            }))
        return defaults

    def _default_get_attendance(self):
        # domain = [('create_date', '<=', datetime.combine(self.date_punch.date(), time(23,59,59))),
        #           ('create_date', '>=', datetime.combine(self.date_punch.date(), time(0,0,0))),
        #           ('employee_id', '=', self.employee_id.id)]
        # domain = [('check_date', '=', datetime.combine(self.date_punch.date(), time(23,59,59))),
        #           ('employee_id', '=', self.employee_id.id)]
        domain = [('check_date', '=', self.request_date_punch),
                  ('employee_id', '=', self.employee_id.id)]
        attendances = self.env['hr.attendance'].read_group(domain, ['ids:array_agg(id)',
                                                                    'check_in',
                                                                    'check_out', 'check_in_issue','check_out_issue',
                                                                    'work_type'],
                                                           ['check_in', 'check_out','check_in_issue','check_out_issue','work_type'],
                                                           lazy=False)
        attendances = sorted(
            [RelenAttendance(group['ids'],group['check_in'], group['check_out'], group['check_in_issue'], group['check_out_issue'],group['work_type'])
             for group in attendances], key=lambda att: (att.work_type))#,reverse=True)

        default_value = RelenAttendance('','', '', 'no check-in','no check-out', 'normal')
        return attendances

    request_date_punch = fields.Date(string='Date')
    yd = fields.Datetime(store=False)
    td = fields.Datetime(store=False)

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', index=True, readonly=True,required=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},default=_default_employee,
        track_visibility='onchange')

    date_punch = fields.Datetime(
        'Punch time', readonly=False, required=True,
        default=fields.Datetime.now,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='confirm',
        help="The status is set to 'To Submit', when a leave request is created." +
             "\nThe status is 'To Approve', when leave request is confirmed by user." +
             "\nThe status is 'Refused', when leave request is refused by manager." +
             "\nThe status is 'Approved', when leave request is approved by manager.")
    user_id = fields.Many2one('res.users', string='User', related_sudo=True, compute_sudo=True, store=True,
                              default=lambda self: self.env.uid, readonly=True)
    attendance_id = fields.Many2one(
        "hr.attendance", string="Attendance", index=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})

    manager_id = fields.Many2one('hr.employee', string='Manager', readonly=True)
    department_id = fields.Many2one(
        'hr.department', string='Department', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    punch_note = fields.Text('Description')
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})

    first_approver_id = fields.Many2one(
        'hr.employee', string='First Approval', readonly=True, copy=False,
        help='This area is automatically filled by the user who validate the leave', oldname='manager_id')

    second_approver_id = fields.Many2one(
        'hr.employee', string='Second Approval', readonly=True, copy=False, oldname='manager_id2',
        help='This area is automaticly filled by the user who validate the leave with second level (If Leave type need second validation)')

    can_reset = fields.Boolean('Can reset', compute='_compute_can_reset')
    can_approve = fields.Boolean('Can Approve', compute='_compute_can_approve')

    work_type = fields.Selection([
        ('normal', 'Normal'),
        ('overtime', 'Overtime'),
    ], string='Work type', track_visibility='onchange', copy=False)
    # work_type_display = fields.Selection([
    #     ('normal', 'Normal'),
    #     ('overtime', 'Overtime'),
    # ], string='Work type', copy=False, readonly=True, store=False,
    #     compute="_compute_work_type_display")
    check_type = fields.Selection([
        ('check-in', 'Check-in'),
        ('check-out', 'Check-out'),
    ], string='Check type', track_visibility='onchange', copy=False)
    work_abnormal = fields.Selection(selection=[
        ('no check-in', 'No check-in'),
        ('no check-out', 'No check-out'),
        ('delay', 'Delay'),
        ('leave early', 'Leave early'),
        ('delay,leave early', 'Delay,Leave early'),
        ('delay,no check-out', 'Delay,No check-out'),
        ('no check-in,no check-out', 'No check-in,No check-out'),
        ('no check-in,leave early', 'No check-in,Leave early')
    ], string="Work abnormal", store=True)
    work_abnormal_display = fields.Selection(selection=[
        ('no check-in', 'No check-in'),
        ('no check-out', 'No check-out'),
        ('delay', 'Delay'),
        ('leave early', 'Leave early'),
        ('delay,leave early', 'Delay,Leave early'),
        ('delay,no check-out', 'Delay,No check-out'),
        ('no check-in,no check-out', 'No check-in,No check-out'),
        ('no check-in,leave early', 'No check-in,Leave early')
    ], string="Work abnormal", compute="_compute_work_abnormal_display", store=False, readonly=True)
    patch_card = fields.Datetime(
        'Patch card', readonly=False, index=True, copy=False, required=True,
        default=fields.Datetime.now(),
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')

    check_time = fields.Datetime(string="Check time")
    check_time_display = fields.Datetime(string="Check time", store=False, readonly=True,
                                         compute="_compute_check_time_display")
    source = fields.Selection(selection=[('machine', 'Machine'),('relenishment','Relenishment')], string="Source")
    source_display = fields.Selection(selection=[('machine', 'Machine'),('relenishment','Relenishment')], string="Source", store=False, readonly=True,
                                      compute="_compute_source_display")

    parent_id = fields.Many2one('hr.replenishment', string='Parent', copy=False)
    linked_request_ids = fields.One2many('hr.replenishment', 'parent_id', string='Linked Requests')

    # relenishment_type=fields.Selection(selection=[
    #     ('employee','By Employee'),
    #     ('company', 'By Company'),
    #     ('department', 'By Department')
    # ],default="employee",string="model",required=True)


    #########################
    #       UI method       #
    #########################
    @api.multi
    @api.onchange('work_abnormal')
    @api.depends('work_abnormal_display')
    def _compute_work_abnormal_display(self):
        for replenishment in self:
            replenishment.work_abnormal_display = replenishment.work_abnormal

    @api.multi
    @api.onchange('check_time')
    @api.depends('check_time_display')
    def _compute_check_time_display(self):
        for replenishment in self:
            replenishment.check_time_display = replenishment.check_time

    @api.multi
    @api.onchange('source')
    @api.depends('source_display')
    def _compute_source_display(self):
        for replenishment in self:
            replenishment.source_display = replenishment.source

    # @api.multi
    # @api.onchange('work_type')
    # @api.depends('work_type_display')
    # def _compute_work_type_display(self):
    #     for replenishment in self:
    #         replenishment.work_type_display = replenishment.work_type


    ####################################################################

    def _convert_date_to_yd_td(self):
        if self.request_date_punch == False:
            return False
        self.yd = datetime(self.request_date_punch.year, self.request_date_punch.month, self.request_date_punch.day, 0, 0, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
        self.td = datetime(self.request_date_punch.year, self.request_date_punch.month, self.request_date_punch.day, 23, 59, 59, 0).strftime("%Y-%m-%d %H:%M:%S")

    def _clear_UI_Data(self):
        self.work_abnormal=False
        self.check_time=False
        self.source=False
        self.work_type=False
        self.attendance_id=False

    @api.onchange('request_date_punch', 'employee_id')
    def onchange_date(self):
        self._clear_UI_Data()
        self._convert_date_to_yd_td()
        self._onchange_request_date_punch()
        if self.check_type == 'check-in':
            self.work_abnormal = 'no check-in'
        if self.check_type == 'check-out':
            self.work_abnormal = 'no check-out'
        res = {}
        if self.request_date_punch and self.employee_id:
            # res['domain'] = {'attendance_id': [('create_date', '>=', self.yd),
            #                                    ('create_date', '<', self.td),
            #                                    ('employee_id', '=', self.employee_id.id)]}
            res['domain'] = {'attendance_id': [('check_date', '=', self.request_date_punch),
                                               ('employee_id', '=', self.employee_id.id)]}
        return res

    @api.onchange('attendance_id')
    def _onchange_attendance_id(self):
        self.source = self.attendance_id.source
        self.work_type = self.attendance_id.work_type
        self.work_abnormal = self.attendance_id.work_abnormal
        if self.work_abnormal == 'no check-in':
            self.check_type = 'check-in'
            self.check_time = self.attendance_id.check_in
        elif self.work_abnormal == 'no check-out':
            self.check_type = 'check-out'
            self.check_time = self.attendance_id.check_out
        else:
            self.check_type = 'check-in'
            self.check_time = self.attendance_id.check_in

    @api.onchange('check_type')
    def _onchange_check_type(self):
        if self.check_type == 'check-in' and self.attendance_id:
            self.check_time = self.attendance_id.check_in
        if self.check_type == 'check-out' and self.attendance_id:
            self.check_time = self.attendance_id.check_out
        if self.check_type == 'check-in':
            self.work_abnormal = 'no check-in'
        if self.check_type == 'check-out':
            self.work_abnormal = 'no check-out'
    ###############################################################

    @api.onchange('request_date_punch','employee_id')
    def _onchange_request_date_punch(self):
        if not self.request_date_punch:
            self.date_punch = False
            return
        # else:
        #     self.patch_card = datetime.strptime(str(self.date_punch), '%Y-%m-%d %H:%M:%S')
        self.date_punch = datetime.strptime(str(self.request_date_punch), '%Y-%m-%d')
        dt = datetime.now().time()
        self.patch_card = datetime.combine(self.date_punch.date(), dt)
        attendances = self._default_get_attendance()


        if str(attendances).strip() == "":
            self.attendance_id = False
        bHaveNormal = False
        for attendance in attendances:

            if attendance.work_type == 'normal':
                bHaveNormal = True

                if attendance.check_in_issue == 'no check-in':
                    replenishment = self.env['hr.replenishment'].search(
                        [('request_date_punch', '=', self.date_punch.date()),
                         ('work_type', '=', attendance.work_type),
                         ('employee_id', '=', self.employee_id.id),
                         ('work_abnormal', '=', attendance.check_in_issue)
                         ], limit=1)

                    if not replenishment.id:
                        self.attendance_id = attendance.id[0]
                        self.source = self.attendance_id.source
                        self.work_abnormal = self.attendance_id.check_in_issue
                        self.work_type = self.attendance_id.work_type
                        self.check_type = 'check-in'
                        break
                elif attendance.check_out_issue == 'no check-out':
                    replenishment = self.env['hr.replenishment'].search(
                        [('request_date_punch', '=', self.date_punch.date()),
                         ('work_type', '=', attendance.work_type),
                         ('employee_id', '=', self.employee_id.id),
                         ('work_abnormal', '=', attendance.check_out_issue)
                         ], limit=1)
                    if not replenishment.id:
                        self.attendance_id = attendance.id[0]
                        self.source = self.attendance_id.source
                        self.work_abnormal = self.attendance_id.check_out_issue
                        self.work_type = self.attendance_id.work_type
                        self.check_type = 'check-out'
                        break
                    else:
                        continue
            if attendance.work_type == 'overtime':
                if attendance.check_in_issue == 'no check-in':
                    replenishment = self.env['hr.replenishment'].search(
                        [('request_date_punch', '=', self.date_punch.date()),
                         ('work_type', '=', attendance.work_type),
                         ('employee_id', '=', self.employee_id.id),
                         ('work_abnormal', '=', attendance.check_in_issue)
                         ], limit=1)
                    if not replenishment.id:
                        self.attendance_id = attendance.id[0]
                        self.source = self.attendance_id.source
                        self.work_abnormal = self.attendance_id.check_in_issue
                        self.work_type = self.attendance_id.work_type
                        self.check_type = 'check-in'
                        break
                elif attendance.check_out_issue == 'no check-out':
                    replenishment = self.env['hr.replenishment'].search(
                        [('request_date_punch', '=', self.date_punch.date()),
                         ('work_type', '=', attendance.work_type),
                         ('employee_id', '=', self.employee_id.id),
                         ('work_abnormal', '=', attendance.check_out_issue)
                         ], limit=1)
                    if not replenishment.id:
                        self.attendance_id = attendance.id[0]
                        self.source = self.attendance_id.source
                        self.work_abnormal = self.attendance_id.check_out_issue
                        self.work_type = self.attendance_id.work_type
                        self.check_type = 'check-out'
                        break
                    else:
                        continue
        if not bHaveNormal:
            domain = [('dayofweek', '=', self.date_punch.date().weekday())]
            weekwork = self.env['resource.calendar.attendance'].read_group(domain, ['ids:array_agg(id)',
                                                                                    'dayofweek', ], ['dayofweek'],
                                                                           lazy=False)
            if weekwork:
                strIssue = 'no check-in'
                strWorkType = 'normal'
                replenishment = self.env['hr.replenishment'].search(
                    [('request_date_punch', '=', self.date_punch.date()),
                     ('work_type', '=', strWorkType),
                     ('employee_id', '=', self.employee_id.id),
                     ('work_abnormal', '=', strIssue)
                     ], limit=1)
                if not replenishment.id:
                    self.source = 'machine'
                    self.work_abnormal = strIssue
                    self.work_type = strWorkType
                    self.check_type = 'check-in'
                else:
                    strIssue = 'no check-out'
                    replenishment = self.env['hr.replenishment'].search(
                        [('request_date_punch', '=', self.date_punch.date()),
                         ('work_type', '=', strWorkType),
                         ('employee_id', '=', self.employee_id.id),
                         ('work_abnormal', '=', strIssue)
                         ], limit=1)
                    if not replenishment.id:
                        self.source = 'machine'
                        self.work_abnormal = strIssue
                        self.work_type = strWorkType
                        self.check_type = 'check-out'
            else:
                strIssue = 'no check-in'
                strWorkType = 'overtime'
                replenishment = self.env['hr.replenishment'].search(
                    [('request_date_punch', '=', self.date_punch.date()),
                     ('work_type', '=', strWorkType),
                     ('employee_id', '=', self.employee_id.id),
                     ('work_abnormal', '=', strIssue)
                     ], limit=1)
                if not replenishment.id:
                    self.source = 'machine'
                    self.work_abnormal = strIssue
                    self.work_type = strWorkType
                    self.check_type = 'check-in'
                else:
                    strIssue = 'no check-out'
                    replenishment = self.env['hr.replenishment'].search(
                        [('request_date_punch', '=', self.date_punch.date()),
                         ('work_type', '=', strWorkType),
                         ('employee_id', '=', self.employee_id.id),
                         ('work_abnormal', '=', strIssue)
                         ], limit=1)
                    if not replenishment.id:
                        self.source = 'machine'
                        self.work_abnormal = strIssue
                        self.work_type = strWorkType
                        self.check_type = 'check-out'


    ###############################################################
    @api.multi
    def _sync_employee_details(self):
        for replenishment in self:
            replenishment.manager_id = replenishment.employee_id.parent_id.id
            if replenishment.employee_id:
                replenishment.department_id = replenishment.employee_id.department_id

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self._sync_employee_details()

    @api.multi
    @api.depends('state', 'employee_id', 'department_id')
    def _compute_can_reset(self):
        for replenishment in self:
            try:
                replenishment._check_approval_update('draft')
            except (AccessError, UserError):
                replenishment.can_reset = False
            else:
                replenishment.can_reset = True

    @api.depends('state', 'employee_id', 'department_id')
    def _compute_can_approve(self):
        for replenishment in self:
            try:
                # if replenishment.state == 'confirm':
                #     replenishment._check_approval_update('validate1')
                # else:
                replenishment._check_approval_update('validate')
            except (AccessError, UserError):
                replenishment.can_approve = False
            else:
                replenishment.can_approve = True

    @api.constrains('request_date_punch')
    def _check_date(self):
        for replenishment in self:
            domain = [
                ('request_date_punch', '=', replenishment.request_date_punch),
                ('work_type', '=', replenishment.work_type),
                ('employee_id', '=', replenishment.employee_id.id),
                ('id', '!=', replenishment.id),
                ('work_abnormal','=',replenishment.work_abnormal),
                ('state', 'not in', ['cancel', 'refuse']),
            ]
            nreplenishment = self.search_count(domain)
            if nreplenishment:
                raise ValidationError(_('You can not have 2 requests that overlaps on the same time.'))

    @api.multi
    def name_get(self):
        result = []
        for replenishment in self:
            result.append((replenishment.id, _("%(empl_name)s : %(patch_card)s for %(check_type)s") % {
                'empl_name': replenishment.employee_id.name,
                'patch_card': replenishment.patch_card,
                'check_type': replenishment.check_type,
            }))
        return result

    @api.multi
    def add_follower(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        if employee.user_id:
            self.message_subscribe(partner_ids=employee.user_id.partner_id.ids)

    @api.model
    def create(self, values):
        """ Override to avoid automatic logging of creation """
        employee_id = values.get('employee_id', False)
        if not values.get('department_id'):
            values.update({'department_id': self.env['hr.employee'].browse(employee_id).department_id.id})
        replenishment = super(HrReplenishment,
                              self.with_context(mail_create_nolog=True, mail_create_nosubscribe=True)).create(values)
        replenishment.add_follower(employee_id)
        if 'employee_id' in values:
            replenishment._sync_employee_details()
        if not self._context.get('import_file'):
            replenishment.activity_update()
        return replenishment

    def _read_from_database(self, field_names, inherited_field_names=[]):
        if 'name' in field_names and 'employee_id' not in field_names:
            field_names.append('employee_id')
        super(HrReplenishment, self)._read_from_database(field_names, inherited_field_names)
        if 'name' in field_names:
            if self.user_has_groups('hr_attendance.group_hr_attendance_user'):
                return
            current_employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
            for record in self:
                emp_id = record._cache.get('employee_id', False) and record._cache.get('employee_id')[0]
                if emp_id != current_employee.id:
                    try:
                        record._cache['name']
                        record._cache['name'] = '*****'
                    except Exception:
                        # skip SpecialValue (e.g. for missing record or access right)
                        pass

    @api.multi
    def write(self, values):
        employee_id = values.get('employee_id', False)
        if values.get('state'):
            self._check_approval_update(values['state'])
        result = super(HrReplenishment, self).write(values)
        self.add_follower(employee_id)
        if 'employee_id' in values:
            self._sync_employee_details()
        return result

    @api.multi
    def unlink(self):
        for replenishment in self.filtered(
                lambda replenishment: replenishment.state not in ['draft', 'cancel', 'confirm']):
            raise UserError(_('You cannot delete a replenishment which is in %s state.') % (replenishment.state,))
        return super(HrReplenishment, self).unlink()

    @api.multi
    def copy_data(self, default=None):
        raise UserError(_('A replenishment cannot be duplicated.'))

    @api.multi
    def _prepare_replenishment_values(self, employee):
        self.ensure_one()
        values = {
            'date_punch': self.date_punch,
            'punch_note': self.punch_note,
            'work_type': self.work_type,
            'check_time': self.check_time,
            'work_abnormal': self.work_abnormal,
            'source': self.source,
            'patch_card': self.patch_card,
            'parent_id': self.id,
            'employee_id': employee.id
        }
        return values

    @api.multi
    def action_draft(self):
        for replenishment in self:
            if replenishment.state not in ['confirm', 'refuse']:
                raise UserError(
                    _('Replenishment request state must be "Refused" or "To Approve" in order to be reset to draft.'))
            replenishment.write({
                'state': 'draft',
                'first_approver_id': False,
                'second_approver_id': False,
            })
            linked_requests = replenishment.mapped('linked_request_ids')
            for linked_request in linked_requests:
                linked_request.action_draft()
            linked_requests.unlink()
        self.activity_update()
        return True

    @api.multi
    def action_confirm(self):
        if self.filtered(lambda replenishment: replenishment.state != 'draft'):
            raise UserError(_('Replenishment request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm'})
        self.activity_update()
        return True

    @api.multi
    def action_approve(self):
        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if any(replenishment.state != 'confirm' for replenishment in self):
            raise UserError(_('Replenishment request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        self.write({'state': 'validate1', 'first_approver_id': current_employee.id})
        self.activity_update()
        return True

    @api.multi
    def action_validate(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if any(replenishment.state not in ['confirm', 'validate1'] for replenishment in self):
            raise UserError(_('Replenishment request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})
        self.write({'second_approver_id': current_employee.id})

        if not self.env.context.get('leave_fast_create'):
            self.activity_update()
        bHaveAtten = False
        if self.attendance_id and self.attendance_id.work_type==self.work_type:
            bHaveAtten = True
            if self.work_type == 'normal' or self.work_type == 'overtime':
                if self.work_abnormal == 'no check-in':
                    attendance = self.env['hr.attendance'].search([
                        ('id', '=', self.attendance_id.id),
                        ('work_type','=',self.work_type)
                    ])
                    attendance.write({'check_in': self.patch_card
                                        ,'check_in_issue': None
                                      })
                elif self.work_abnormal == 'no check-out':
                    attendance = self.env['hr.attendance'].search([
                        ('id', '=', self.attendance_id.id),
                        ('work_type', '=', self.work_type)
                    ])
                    attendance.write({'check_out': self.patch_card
                                         , 'check_out_issue': None
                                      })
        else:
            rattendances = self._default_get_attendance()
            for rattendance in rattendances:
                self.attendance_id = rattendance.id[0]
                if self.attendance_id and self.attendance_id.work_type==self.work_type:
                    bHaveAtten = True
                    if self.work_type == 'normal' or self.work_type == 'overtime':
                        if self.work_abnormal == 'no check-in':
                            attendance = self.env['hr.attendance'].search([
                                ('id', '=', self.attendance_id.id),
                                ('work_type', '=', self.work_type)
                            ])
                            if attendance.check_in:
                                continue
                            else:
                                attendance.write({'check_in': self.patch_card
                                                     , 'check_in_issue': None
                                                  })
                        elif self.work_abnormal == 'no check-out':
                            attendance = self.env['hr.attendance'].search([
                                ('id', '=', self.attendance_id.id),
                                ('work_type', '=', self.work_type)
                            ])
                            if attendance.check_out:
                                continue
                            else:
                                attendance.write({'check_out': self.patch_card
                                                     , 'check_out_issue': None
                                                  })
                # else:
                #     values = self._prepare_attendance_values()
                #     attendanceid = self.env['hr.attendance'].with_context(beNew_record=True).create(values)
                #     self.write({'attendance_id': attendanceid.id})
        if not bHaveAtten:
            values = self._prepare_attendance_values()
            attendanceid = self.env['hr.attendance'].with_context(beNew_record=True).create(values)
            self.write({'attendance_id': attendanceid.id})

        # self._validate_leave_request()
        # if not self.env.context.get('leave_fast_create'):
        #     employee_requests.activity_update()
        return True

    @api.multi
    def action_refuse(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for replenishment in self:
            if replenishment.state not in ['confirm', 'validate', 'validate1']:
                raise UserError(_('replenishment request must be confirmed or validated in order to refuse it.'))

            if replenishment.state == 'validate1':
                replenishment.write({'state': 'refuse', 'first_approver_id': current_employee.id})
            else:
                replenishment.write({'state': 'refuse', 'second_approver_id': current_employee.id})
            replenishment.linked_request_ids.action_refuse()
            attendance = self.env['hr.attendance'].search([
                ('id', '=', self.attendance_id.id),
            ])
            if (self.work_abnormal == 'no check-in' and not attendance.check_out) or (
                    self.work_abnormal == 'no check-out' and not attendance.check_in):
                attendance.unlink()
            elif self.work_abnormal == 'no check-in' and attendance.check_out:
                attendance.write({'check_in': None
                                     , 'check_in_issue': 'no check-in'
                                  })
            elif self.work_abnormal == 'no check-out' and attendance.check_in:
                attendance.write({'check_out': None
                                     , 'check_out_issue': 'no check-out'
                                  })
        # self._remove_resource_leave()
        self.activity_update()
        return True

    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        is_officer = self.env.user.has_group('hr_attendance.group_hr_attendance')
        is_manager = self.env.user.has_group('hr_attendance.group_hr_attendance_user')
        for replenishment in self:
            if state == 'confirm':
                continue

            if state == 'draft':
                if replenishment.employee_id != current_employee and not is_manager:
                    raise UserError(_('Only a replenishment Manager can reset other people leaves.'))
                continue

            if not is_officer:
                raise UserError(_('Only a replenishment Officer or Manager can approve or refuse leave requests.'))

            if is_officer:
                # use ir.rule based first access check: department, members, ... (see security.xml)
                replenishment.check_access_rule('write')

            if replenishment.employee_id == current_employee and not is_manager:
                raise UserError(_('Only a replenishment Manager can approve its own requests.'))

            if (state == 'validate1') or (state == 'validate'):
                manager = replenishment.employee_id.parent_id or replenishment.employee_id.department_id.manager_id
                if (manager and manager != current_employee) and not self.env.user.has_group(
                        'hr_attendance.group_hr_attendance_user'):
                    raise UserError(_('You must be either %s\'s manager or Leave manager to approve this leave') % (
                        replenishment.employee_id.name))

            if state == 'validate':
                if not self.env.user.has_group('hr_attendance.group_hr_attendance_user'):
                    raise UserError(_('Only an Leave replenishment can apply the second approval on leave requests.'))

    def _get_responsible_for_approval(self):
        if self.state == 'confirm' and self.manager_id.user_id:
            return self.manager_id.user_id
        elif self.state == 'confirm' and self.employee_id.parent_id.user_id:
            return self.employee_id.parent_id.user_id
        elif self.department_id.manager_id.user_id:
            return self.department_id.manager_id.user_id
        return self.env['res.users']

    def activity_update(self):
        to_clean, to_do = self.env['hr.replenishment'], self.env['hr.replenishment']
        for replenishment in self:
            if replenishment.state == 'draft':
                to_clean |= replenishment
            elif replenishment.state == 'confirm':
                replenishment.activity_schedule(
                    'hr_attendance_extend.mail_act_replenishment_approval',
                    user_id=replenishment.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif replenishment.state == 'validate1':
                replenishment.activity_feedback(['hr_attendance_extend.mail_act_leave_approval'])
                replenishment.activity_schedule(
                    'hr_attendance_extend.mail_act_replenishment_second_approval',
                    user_id=replenishment.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif replenishment.state == 'validate':
                to_do |= replenishment
            elif replenishment.state == 'refuse':
                to_clean |= replenishment
        if to_clean:
            to_clean.activity_unlink(['hr_attendance_extend.mail_act_replenishment_approval',
                                      'hr_attendance_extend.mail_act_replenishment_second_approval'])
        if to_do:
            to_do.activity_feedback(['hr_attendance_extend.mail_act_replenishment_approval',
                                     'hr_attendance_extend.mail_act_replenishment_second_approval'])

    ####################################################
    # Messaging methods
    ####################################################

    @api.multi
    def _track_subtype(self, init_values):
        if 'state' in init_values and self.state == 'validate':
            return 'hr_attendance_extend.mt_replenishment_approved'
        elif 'state' in init_values and self.state == 'refuse':
            return 'hr_attendance_extend.mt_replenishment_refused'
        return super(HrReplenishment, self)._track_subtype(init_values)

    @api.multi
    def _notify_get_groups(self, message, groups):
        """ Handle HR users and officers recipients that can validate or refuse replenishments
        directly from email. """
        groups = super(HrReplenishment, self)._notify_get_groups(message, groups)

        self.ensure_one()
        hr_actions = []
        if self.state == 'confirm':
            app_action = self._notify_get_action_link('controller', controller='/Replenishment/validate')
            hr_actions += [{'url': app_action, 'title': _('Approve')}]
        if self.state in ['confirm', 'validate', 'validate1']:
            ref_action = self._notify_get_action_link('controller', controller='/Replenishment/refuse')
            hr_actions += [{'url': ref_action, 'title': _('Refuse')}]

        attendance_user_group_id = self.env.ref('hr_attendance.group_hr_attendance_user').id
        new_group = (
            'group_hr_attendance_user',
            lambda pdata: pdata['type'] == 'user' and attendance_user_group_id in pdata['groups'], {
                'actions': hr_actions,
            })

        return [new_group] + groups

    @api.multi
    def message_subscribe(self, partner_ids=None, channel_ids=None, subtype_ids=None):
        # due to record rule can not allow to add follower and mention on validated leave so subscribe through sudo
        if self.state in ['validate', 'validate1']:
            self.check_access_rights('read')
            self.check_access_rule('read')
            return super(HrReplenishment, self.sudo()).message_subscribe(partner_ids=partner_ids,
                                                                         channel_ids=channel_ids,
                                                                         subtype_ids=subtype_ids)
        return super(HrReplenishment, self).message_subscribe(partner_ids=partner_ids, channel_ids=channel_ids,
                                                              subtype_ids=subtype_ids)

    @api.multi
    def _prepare_attendance_values(self):
        self.ensure_one()
        values = {
            'employee_id': self.employee_id.id,
            'check_in': self.patch_card,
            'worked_hours': 0,
            'work_type': self.work_type,
            'late_time': 0,
            'leave_early_time': 0,
            'source':'relenishment',
            'check_out_issue': 'no check-out',
            'work_abnormal': self.work_abnormal,
            'check_date':self.request_date_punch
        }
        return values
