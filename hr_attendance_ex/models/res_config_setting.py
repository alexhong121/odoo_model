# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.multi
    def comparison_table(self):

        return {
            'name': 'vacation days comparison table',
            'type': 'ir.actions.client',
            'tag': 'mc_vacation_days_comparison_table',
            'target': 'new',
        }
