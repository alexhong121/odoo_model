# -*- coding: utf-8 -*-
from datetime import timedelta
from pytz import timezone, UTC
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, MissingError, Warning, ValidationError
from odoo.tools import float_compare

class HolidaysRequest(models.Model):
    _inherit = 'hr.leave'

    # override
    @api.model
    def default_get(self, fields_list):
        defaults = super(HolidaysRequest, self).default_get(fields_list)
        defaults['holiday_status_id'] = False
        return defaults

    def _default_get_request_parameters(self, values):
        new_values = dict(values)
        global_from, global_to = False, False
        # TDE FIXME: consider a mapping on several days that is not the standard
        # calendar widget 7-19 in user's TZ is some custom input
        if values.get('date_from'):
            user_tz = self.env.user.tz or 'UTC'
            localized_dt = timezone('UTC').localize(values['date_from']).astimezone(timezone(user_tz))
            global_from = localized_dt.time().hour == 7 and localized_dt.time().minute == 0
            values['date_from']=localized_dt
            new_values['request_date_from'] = values['date_from'].date()
        if values.get('date_to'):
            user_tz = self.env.user.tz or 'UTC'
            localized_dt = timezone('UTC').localize(values['date_to']).astimezone(timezone(user_tz))
            global_to = localized_dt.time().hour == 19 and localized_dt.time().minute == 0
            new_values['request_date_to'] = values['date_to'].date()
        if global_from and global_to:
            new_values['request_unit_custom'] = True
        return new_values

    allocation_id = fields.Many2one('hr.leave.allocation', string="準假單")
    allocation_type = fields.Selection('Allocation Type', related='holiday_status_id.allocation_type')
    validity_interval_type = fields.Selection(
        related='holiday_status_id.validity_interval_type',
        string='准假時長'
    )
    allocation_id_hide=fields.Boolean(computer='_compute_allocation_id_hide')

    #################################
    #       invisible method        #
    #################################
    @api.model
    @api.onchange('holiday_status_id')
    @api.depends('holiday_status_id')
    def _compute_allocation_id_hide(self):
        if self.allocation_type=='no' or self.holiday_status_id.id is False:
            self.allocation_id_hide=True
        else:
            self.allocation_id_hide=False

    ###############################
    #       Activity method       #
    ###############################
    @api.multi
    @api.onchange('holiday_status_id', 'allocation_id', 'mode_company_id', 'department_id', 'category_id',
                  'employee_id')
    @api.depends('holiday_status_id')
    def _assign_allocation(self):
        res = {}
        holiday_status = self.holiday_status_id.id
        allocations = self.env['hr.leave.allocation'].search(
            [('holiday_type', '=', self.holiday_type),
             ('holiday_status_id', '=', holiday_status),
             ('mode_company_id', '=', self.mode_company_id.id),
             ('category_id', '=', self.category_id.id),
             ('employee_id', '=', self.employee_id.id),
             ('state', 'in', ('validate', 'validate1')),
             ('validity_stop', '>=', fields.date.today())])

        res['domain'] = {'allocation_id': [('id', 'in', allocations.ids), ('state', 'in', ('validate', 'validate1'))]}
        return res

    @api.onchange('holiday_status_id')
    def _pass_to_allocation_id(self):
        if self.holiday_status_id.id is False:
            self.allocation_id = False
            return False
        else:
            allocation = self.env['hr.leave.allocation'].search([
                ('holiday_status_id', '=', self.holiday_status_id.id),
                ('validity_stop', '>=', fields.date.today()),
                ('state', 'in', ('validate', 'validate1')),
                ('employee_id', '=', self.employee_id.id)
            ], limit=1)
            self.allocation_id = allocation.id

    #####################################
    #       Business logic method       #
    #####################################

    # override
    @api.multi
    @api.constrains('allocation_id', 'date_to', 'date_from')
    def _check_leave_type_validity(self):
        for leave in self:
            if leave.allocation_id.validity_start and leave.allocation_id.validity_stop:
                vstart = leave.allocation_id.validity_start
                vstop = leave.allocation_id.validity_stop
                dfrom = leave.date_from
                dto = leave.date_to

                if dfrom and dto and (dfrom.date() < vstart or dto.date() > vstop):
                    raise UserError(
                        _('You can take %s only between %s and %s') % (
                            leave.allocation_id.display_name, leave.allocation_id.validity_start,
                            leave.allocation_id.validity_stop))

    # override
    @api.constrains('state', 'number_of_days', 'allocation_id')
    def _check_holidays(self):
        for holiday in self:
            if holiday.holiday_type != 'employee' or not holiday.employee_id or holiday.allocation_type == 'no':
                continue
            leave_days = holiday.allocation_id.get_days(holiday.employee_id.id)[holiday.allocation_id.id]
            if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or \
              float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                        'Please also check the leaves waiting for validation.'))
    # override
    @api.multi
    def _prepare_holiday_values(self, employee):
        self.ensure_one()
        if self.allocation_type != 'no':
            allocation = self._check_batch(employee)
        values = {
            'name': self.name,
            'holiday_type': 'employee',
            'holiday_status_id': self.holiday_status_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'request_date_from': self.date_from,
            'request_date_to': self.date_to,
            'notes': self.notes,
            'number_of_days': employee.get_work_days_data(self.date_from, self.date_to)['days'],
            'parent_id': self.id,
            'employee_id': employee.id,
            'allocation_id': allocation.id if self.allocation_type != 'no' else False
        }
        return values

    @api.multi
    def _check_batch(self, employee):
        self.ensure_one()
        allocations = self.env['hr.leave.allocation'].search(
            [('holiday_status_id', '=', self.holiday_status_id.id),
             ('employee_id', '=', employee.id),
             ('name', '=', self.allocation_id.name)
             ])
        if allocations.id is False:
            raise UserError('%s沒有"%s"準假單　無法請假' % (employee.name, self.allocation_id.name))
        return allocations
