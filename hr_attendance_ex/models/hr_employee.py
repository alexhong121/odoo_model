import logging

from odoo import models, fields, api, _, SUPERUSER_ID,exceptions
from odoo.exceptions import UserError, AccessError, MissingError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"
    _sql_constraints = [('check_machine_ID', 'UNIQUE(machine_ID)', '考勤機ID 編號已經有其他員工使用,不可以重複！')]

    due_date = fields.Date(string='到職日')
    machine_id = fields.Char(string='考勤機ID')

    @api.multi
    def attendance_overtime_manual(self, next_action, entered_pin=None):
        self.ensure_one()
        if not (entered_pin is None) or self.env['res.users'].browse(SUPERUSER_ID).has_group(
                'hr_attendance.group_hr_attendance_use_pin') and (
                self.user_id and self.user_id.id != self._uid or not self.user_id):
            if entered_pin != self.pin:
                return {'warning': _('Wrong PIN')}
        return self.attendance_overtime_action(next_action)

    @api.multi
    def attendance_overtime_action(self, next_action):
        """ Changes the attendance of the employee.
            Returns an action to the check in/out message,
            next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
        """
        self.ensure_one()
        action_message = self.env.ref('hr_attendance.hr_attendance_action_greeting_message').read()[0]
        action_message['previous_attendance_change_date'] = self.last_attendance_id and (
                    self.last_attendance_id.check_out or self.last_attendance_id.check_in) or False
        action_message['employee_name'] = self.name
        action_message['barcode'] = self.barcode
        action_message['next_action'] = next_action

        if self.user_id:

            print(self.sudo(self.user_id.id))
            modified_attendance = self.sudo(self.user_id.id).attendance_overtime_action_change()
        else:
            modified_attendance = self.sudo().attendance_overtime_action_change()
        action_message['attendance'] = modified_attendance.read()[0]
        return {'action': action_message}

    @api.multi
    def attendance_overtime_action_change(self):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        if len(self) > 1:
            raise exceptions.UserError(_('Cannot perform check in or check out on multiple employees.'))
        action_date = fields.Datetime.now()
        if self.attendance_state != 'checked_in':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
                'work_type': 'overtime'
            }
            return self.env['hr.attendance'].create(vals)
        else:
            attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False),('work_type','=','overtime')],
                                                          limit=1)
            if attendance:
                attendance.check_out = action_date
            else:
                raise exceptions.UserError(
                    _('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                      'Your attendances have probably been modified manually by human resources.') % {
                        'empl_name': self.name, })
            return attendance

    #overwrite
    @api.multi
    def attendance_action_change(self):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        if len(self) > 1:
            raise exceptions.UserError(_('Cannot perform check in or check out on multiple employees.'))
        action_date = fields.Datetime.now()

        if self.attendance_state != 'checked_in':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
            }
            return self.env['hr.attendance'].create(vals)
        else:
            attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False),('work_type','=','normal')], limit=1)
            if attendance:
                attendance.check_out = action_date
            else:
                raise exceptions.UserError(_('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                    'Your attendances have probably been modified manually by human resources.') % {'empl_name': self.name, })
            return attendance
    @api.model_cr
    def init(self):
        pass
