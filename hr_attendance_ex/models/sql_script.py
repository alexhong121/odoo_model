# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, MissingError

_logger = logging.getLogger(__name__)

class SqlScript(models.Model):
    _inherit='sql.config'

    script=fields.Text(string='SQL腳本')

