# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields, api, exceptions

# _logger = logging.getLogger(__name__)

class HrPunchCardRequests(models.Model):
    _name = "hr.pubchcardrequests"
    _description = "PunchCardRequests"
    _order = "date_card desc"

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True,
                                  ondelete='cascade', index=True,default=lambda self:self._default_employee)
    department_id = fields.Many2one(
        'hr.department', string='Department', readonly=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', readonly=True)
    date_card = fields.Datetime(
        'Start Date', readonly=True, index=True, copy=False, required=True,
        default=fields.Datetime.now)
    number_of_cards = fields.Float(
        'Cumulative', copy=False, readonly=True, track_visibility='onchange')
    # department_id = fields.Many2one(
    #     'hr.department', string='Department', readonly=True,
    #     states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    # date_card = fields.Datetime(
    #     'Start Date', readonly=True, index=True, copy=False, required=True,
    #     default=fields.Datetime.now,
    #     states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    # number_of_cards = fields.Float(
    #     'Cumulative', copy=False, readonly=True, track_visibility='onchange',
    #     states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    name = fields.Char('Description')

    user_id = fields.Many2one('res.users', string='User', related_sudo=True, compute_sudo=True, store=True, default=lambda self: self.env.uid, readonly=True)
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
    first_approver_id = fields.Many2one(
        'hr.employee', string='First Approval', readonly=True, copy=False,
        help='This area is automatically filled by the user who validate the leave', oldname='manager_id')
    second_approver_id = fields.Many2one(
        'hr.employee', string='Second Approval', readonly=True, copy=False, oldname='manager_id2',
        help='This area is automaticly filled by the user who validate the leave with second level (If Leave type need second validation)')

    # first_approver_id = fields.Many2one(
    #     'hr.employee', string='First Approval', readonly=True, copy=False,
    #     help='This area is automatically filled by the user who validate the leave')
    # second_approver_id = fields.Many2one(
    #     'hr.employee', string='Second Approval', readonly=True, copy=False,
    #     help='This area is automaticly filled by the user who validate the leave with second level (If Leave type need second validation)')

    # can_reset = fields.Boolean('Can reset', compute='_compute_can_reset')
    # can_approve = fields.Boolean('Can Approve', compute='_compute_can_approve')
    can_reset = fields.Boolean('Can reset')
    can_approve = fields.Boolean('Can Approve')




