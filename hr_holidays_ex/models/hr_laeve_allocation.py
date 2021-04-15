# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, MissingError, Warning
from odoo.tools.float_utils import float_round


class HolidaysAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    _order = 'validity_start asc'

    def _default_validity_start_year(self):
        results = []
        currentYear = int(datetime.datetime.strftime(fields.datetime.now(), '%Y'))
        for i in range(-1, 9):
            tup = (str(currentYear + i), str(currentYear + i))
            results.append(tup)
        return results

    validity_start = fields.Date(string="Start Date",
                                 default=fields.Date.today,
                                 store=True,
                                 help='Adding validity to types of leaves so that it cannot be selected outside this time period')
    validity_stop = fields.Date(string="End Date", store=True)
    job_tenure = fields.Char(string='job_tenure', store=True, readonly=False)
    validity_interval_type = fields.Selection(
        related='holiday_status_id.validity_interval_type',
        string='准假時長',
        store=True
    )
    validity_start_year = fields.Selection(
        selection=lambda self: self._default_validity_start_year(),
        string="有效起始年份",
        default=fields.datetime.now().strftime('%Y'),
        required=True
    )

    max_leaves = fields.Float(compute='_compute_leaves', string='Maximum Allowed',
                              help='This value is given by the sum of all leaves requests with a positive value.')

    leaves_taken = fields.Float(
        compute='_compute_leaves', string='Leaves Already Taken',
        help='This value is given by the sum of all leaves requests with a negative value.')
    remaining_leaves = fields.Float(
        compute='_compute_leaves', string='Remaining Leaves',
        help='Maximum Leaves Allowed - Leaves Already Taken')
    virtual_remaining_leaves = fields.Float(
        compute='_compute_leaves', string='Virtual Remaining Leaves',
        help='Maximum Leaves Allowed - Leaves Already Taken - Leaves Waiting Approval')

    # UI
    validity_start_display = fields.Date(compute="_compute_validity_start_display",
                                         string="validity Start Date display")
    validity_stop_display = fields.Date(compute="_compute_validity_stop_display", string="validity End Date display")
    job_tenure_display = fields.Char(string='年資', store=False, readonly=True, compute="_compute_job_tenure_display")

    number_of_days_hide = fields.Boolean(compute='_compute_days_hide')
    number_of_hours_hide = fields.Boolean(compute='_compute_hours_hide')

    #################################
    #       invisible method        #
    #################################
    @api.onchange('holiday_type', 'holiday_status_id')
    @api.depends('holiday_type', 'holiday_status_id')
    def _compute_days_hide(self):
        if (
                self.type_request_unit == 'day' and self.holiday_type == 'employee') and self.validity_interval_type == 'due_date':
            self.number_of_days_hide = False
        elif (
                self.type_request_unit == 'day' and self.holiday_type == 'employee') and self.validity_interval_type == 'hr_leave_allocation':
            self.number_of_days_hide = False
        elif (
                self.type_request_unit == 'day' and self.holiday_type != 'employee') and self.validity_interval_type == 'hr_leave_allocation':
            self.number_of_days_hide = False
        elif (
                self.type_request_unit == 'day' and self.holiday_type != 'employee') and self.validity_interval_type == 'due_date':
            self.number_of_days_hide = True
            self.number_of_days = False
        else:
            self.number_of_days_hide = True

    @api.onchange('holiday_type', 'holiday_status_id')
    @api.depends('holiday_type', 'holiday_status_id')
    def _compute_hours_hide(self):
        if (
                self.type_request_unit == 'hour' and self.holiday_type == 'employee') and self.validity_interval_type == 'due_date':
            self.number_of_hours_hide = False
        elif (
                self.type_request_unit == 'hour' and self.holiday_type == 'employee') and self.validity_interval_type == 'hr_leave_allocation':
            self.number_of_hours_hide = False
        elif (
                self.type_request_unit == 'hour' and self.holiday_type != 'employee') and self.validity_interval_type == 'hr_leave_allocation':
            self.number_of_hours_hide = False
        elif (
                self.type_request_unit == 'hour' and self.holiday_type != 'employee') and self.validity_interval_type == 'due_date':
            self.number_of_hours_hide = True
            self.number_of_days = False
        else:
            self.number_of_hours_hide = True

    #########################
    #       UI method       #
    #########################
    @api.multi
    @api.depends('validity_start')
    def _compute_validity_start_display(self):
        for allocation in self:
            allocation.validity_start_display = allocation.validity_start

    @api.multi
    @api.depends('validity_stop')
    def _compute_validity_stop_display(self):
        for allocation in self:
            allocation.validity_stop_display = allocation.validity_stop

    @api.multi
    @api.depends('job_tenure')
    def _compute_job_tenure_display(self):
        for allocation in self:
            allocation.job_tenure_display = allocation.job_tenure

    #############################
    #   ORM Overrides methods   #
    #############################
    # override
    @api.multi
    def name_get(self):
        res = []
        if not self._context.get('employee_id'):
            # leave counts is based on employee_id, would be inaccurate if not based on correct employee
            for record in self:
                name = record.name
                res.append((record.id, name))
            return res

        for record in self:
            name = record.name
            if record.holiday_status_id.allocation_type != 'no':
                name = "%(name)s (%(count)s)" % {
                    'name': name,
                    'count': _('剩餘%g ,共%g') % (
                        float_round(record.virtual_remaining_leaves, precision_digits=2) or 0.0,
                        float_round(record.max_leaves, precision_digits=2) or 0.0,
                    ) + (_(' hours') if record.holiday_status_id.request_unit == 'hour' else _(' days'))
                }
            res.append((record.id, name))

            print(self._context.get('holiday_type'))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self._context.get('holiday_status_id',False):
            args=self._get_search_args(args,self.env,self._context)
            return super().name_search(name, args, operator, limit)
        else:
            return super().name_search(name, args, operator, limit)

    def _get_search_args(self, args, env, context):
        """
        employee_id
        holiday_status_id
        department_id
        category_id
        mode_company_id
        holiday_type
        :param env:
        :param context:
        :return:
        """
        fields_dict = {'employee_id': context.get('employee_id', False),
                       'holiday_status_id': context.get('holiday_status_id', False),
                       'department_id': context.get('department_id', False),
                       'category_id': context.get('category_id', False),
                       'mode_company_id': context.get('mode_company_id', False),
                       'holiday_type': context.get('holiday_type', False)
                       }

        _allocation_ids=self._get_allocation_ids(env, fields_dict)
        args.append(['id','in',_allocation_ids])
        return args

    def _get_allocation_ids(self, env, fields_dict, context=None):
        model_obj = env['hr.leave.allocation']
        ids = model_obj.search(
            [('holiday_type', '=', fields_dict['holiday_type']),
             ('holiday_status_id', '=', fields_dict['holiday_status_id']),
             ('mode_company_id', '=', fields_dict['mode_company_id']),
             ('category_id', '=', fields_dict['category_id']),
             ('employee_id', '=', fields_dict['employee_id']),
             ('state', 'in', ('validate', 'validate1')),
             ('validity_stop', '>=', fields.date.today())])
        return ids.ids

    @api.constrains('validity_start_year', 'validity_interval_type', 'holiday_type')
    def _check_allocation(self):
        allocations = self.env['hr.leave.allocation'].search(
            [('validity_start_year', '=', self.validity_start_year),
             ('employee_id', '=', self.employee_id.id),
             ('mode_company_id', '=', self.mode_company_id.id),
             ('department_id', '=', self.department_id.id),
             ('category_id', '=', self.category_id.id),
             ('validity_interval_type', '=', 'due_date'),
             ])
        counts=len(allocations)
        if self.holiday_type == 'employee' and counts > 1:
            raise UserError("%s已於%s年產生有效的准假單 不可重複" % (self.employee_id.name, self.validity_start_year))
        elif self.holiday_type == 'company' and counts > 1:
            raise UserError("%s已於%s年產生有效的准假單 不可重複" % (self.mode_company_id.name, self.validity_start_year))

        elif self.holiday_type == 'department' and counts > 1:
            raise UserError("%s已於%s年產生有效的准假單 不可重複" % (self.department_id.name, self.validity_start_year))

        elif self.holiday_type == 'category' and counts > 1:
            raise UserError("%s已於%s年產生有效的准假單 不可重複" % (self.category_id.name, self.validity_start_year))

    ###############################
    #       Activity method       #
    ###############################
    @api.onchange('holiday_status_id', 'employee_id', 'validity_start_year')
    def onchange_holidayStatus_and_employee(self):
        if self.validity_interval_type == 'due_date':
            result = self._compute_holiday_days(self.employee_id)
            if result:
                self.validity_start = result['validity_start']
                self.validity_stop = result['validity_stop']
                self.number_of_days = result['number_of_days']
                self.job_tenure = result['job_tenure']
            else:
                return False

    @api.onchange('holiday_status_id', 'holiday_type', 'validity_start_year')
    def _onchange_holiday_type(self):
        if self.holiday_type != 'employee' and self.validity_interval_type == 'due_date':
            self.validity_start = datetime.date(int(self.validity_start_year), 1, 1)
            self.validity_stop = False

    #####################################
    #       Business logic method       #
    #####################################
    @api.multi
    def _compute_holiday_days(self, employee):
        hr_due_date = employee.due_date
        # 檢查此員工是否有到職日日期
        if hr_due_date is False and employee.id is False:
            return 0
        elif hr_due_date is False:
            raise UserError('%s未填寫到職日' % employee.name)
        else:
            validity_start_year = self.validity_start_year
            job_tenure = self._compute_job_tenure(hr_due_date, validity_start_year)
            if job_tenure > 0:
                validity_start = datetime.date(int(validity_start_year), hr_due_date.month, hr_due_date.day)
                validity_stop = validity_start + relativedelta(years=+1, days=-1)
                number_of_days = self._comparison_number_of_days(job_tenure)
            else:
                validity_start = datetime.date(int(validity_start_year), hr_due_date.month, hr_due_date.day)
                validity_stop = validity_start + relativedelta(months=+6, days=-1)
                number_of_days = self._comparison_number_of_days(job_tenure)
            return {
                'validity_start': validity_start,
                'validity_stop': validity_stop,
                'number_of_days': number_of_days,
                'job_tenure': job_tenure
            }

    def _compute_job_tenure(self, hr_due_date, validity_start_year):
        d1 = datetime.datetime(hr_due_date.year, hr_due_date.month, hr_due_date.day)
        d2 = datetime.datetime(int(validity_start_year), hr_due_date.month, hr_due_date.day)
        times = relativedelta(d2, d1)
        return times.years

    def _comparison_number_of_days(self, job_tenure):
        if job_tenure > 25:
            return 30
        else:
            comparison_table = self.env['vacation.days.comparison'].search([('seniority_val', '=', job_tenure)])
        return comparison_table.value

    # override
    @api.multi
    def _prepare_holiday_values(self, employee):
        self.ensure_one()
        holiday_days = self._compute_holiday_days(employee)
        values = {
            'name': self.name,
            'holiday_type': 'employee',
            'holiday_status_id': self.holiday_status_id.id,
            'notes': self.notes,
            'number_of_days': holiday_days[
                'number_of_days'] if self.validity_interval_type == 'due_date' else self.number_of_days,
            'parent_id': self.id,
            'employee_id': employee.id,
            'accrual': self.accrual,
            'date_to': self.date_to,
            'interval_unit': self.interval_unit,
            'interval_number': self.interval_number,
            'number_per_interval': self.number_per_interval,
            'unit_per_interval': self.unit_per_interval,
            'validity_start': holiday_days[
                'validity_start'] if self.validity_interval_type == 'due_date' else self.validity_start,
            'validity_stop': holiday_days[
                'validity_stop'] if self.validity_interval_type == 'due_date' else self.validity_stop,
            'job_tenure': holiday_days['job_tenure'],
            'validity_start_year': self.validity_start_year
        }
        return values

    def _get_contextual_employee_id(self):
        if 'employee_id' in self._context:
            employee_id = self._context['employee_id']
        elif 'default_employee_id' in self._context:
            employee_id = self._context['default_employee_id']
        else:
            employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1).id
        return employee_id

    @api.multi
    def get_days(self, employee_id):
        # need to use `dict` constructor to create a dict per id
        result = dict(
            (id, dict(max_leaves=0, leaves_taken=0, remaining_leaves=0, virtual_remaining_leaves=0)) for id in self.ids)

        requests = self.env['hr.leave'].search([
            ('employee_id', '=', employee_id),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('allocation_id', 'in', self.ids)
        ])

        for request in requests:
            status_dict = result[request.allocation_id.id]
            status_dict['virtual_remaining_leaves'] -= (request.number_of_hours_display
                                                        if request.leave_type_request_unit == 'hour'
                                                        else request.number_of_days)
            if request.state == 'validate':
                status_dict['leaves_taken'] += (request.number_of_hours_display
                                                if request.leave_type_request_unit == 'hour'
                                                else request.number_of_days)
                status_dict['remaining_leaves'] -= (request.number_of_hours_display
                                                    if request.leave_type_request_unit == 'hour'
                                                    else request.number_of_days)

        for allocation in self:
            status_dict = result[allocation.id]
            if allocation.state == 'validate':
                # note: add only validated allocation even for the virtual
                # count; otherwise pending then refused allocation allow
                # the employee to create more leaves than possible
                status_dict['virtual_remaining_leaves'] += (allocation.number_of_hours_display
                                                            if allocation.type_request_unit == 'hour'
                                                            else allocation.number_of_days)
                status_dict['max_leaves'] += (allocation.number_of_hours_display
                                              if allocation.type_request_unit == 'hour'
                                              else allocation.number_of_days)
                status_dict['remaining_leaves'] += (allocation.number_of_hours_display
                                                    if allocation.type_request_unit == 'hour'
                                                    else allocation.number_of_days)

        return result

    @api.multi
    def _compute_leaves(self):
        data_days = {}
        employee_id = self._get_contextual_employee_id()

        if employee_id:
            data_days = self.get_days(employee_id)

        for holiday_status in self:
            result = data_days.get(holiday_status.id, {})
            holiday_status.max_leaves = result.get('max_leaves', 0)
            holiday_status.leaves_taken = result.get('leaves_taken', 0)
            holiday_status.remaining_leaves = result.get('remaining_leaves', 0)
            holiday_status.virtual_remaining_leaves = result.get('virtual_remaining_leaves', 0)
