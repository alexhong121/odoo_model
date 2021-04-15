# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MsResConfigModuleInstallationMixin(object):
    @api.model
    def _install_modules(self, modules):
        """ Install the requested modules.

        :param modules: a list of tuples (module_name, module_record)
        :return: the next action to execute
        """
        to_install_modules = self.env['ir.module.module']
        to_install_missing_names = []

        for name, module in modules:
            if not module:
                to_install_missing_names.append(name)
            elif module.state == 'uninstalled':
                to_install_modules += module
        result = None
        if to_install_modules:
            result = to_install_modules.button_immediate_install()
        # FIXME: if result is not none, the corresponding todo will be skipped because it was just marked done
        if to_install_missing_names:
            return {
                'type': 'ir.actions.client',
                'tag': 'apps',
                'params': {'modules': to_install_missing_names},
            }

        return result


class McResConfigSettings(models.TransientModel, MsResConfigModuleInstallationMixin):
    """ Base configuration wizard for application settings.  It provides support for setting
        default values, assigning groups to employee users, and installing modules.
        To make such a 'settings' wizard, define a model like::

            class MyConfigWizard(models.TransientModel):
                _name = 'my.settings'
                _inherit = 'res.config.settings'

                default_foo = fields.type(..., default_model='my.model'),
                group_bar = fields.Boolean(..., group='base.group_user', implied_group='my.group'),
                module_baz = fields.Boolean(...),
                config_qux = fields.Char(..., config_parameter='my.parameter')
                other_field = fields.type(...),

        The method ``execute`` provides some support based on a naming convention:

        *   For a field like 'default_XXX', ``execute`` sets the (global) default value of
            the field 'XXX' in the model named by ``default_model`` to the field's value.

        *   For a boolean field like 'group_XXX', ``execute`` adds/removes 'implied_group'
            to/from the implied groups of 'group', depending on the field's value.
            By default 'group' is the group Employee.  Groups are given by their xml id.
            The attribute 'group' may contain several xml ids, separated by commas.

        *   For a selection field like 'group_XXX' composed of 2 integers values ('0' and '1'),
            ``execute`` adds/removes 'implied_group' to/from the implied groups of 'group',
            depending on the field's value.
            By default 'group' is the group Employee.  Groups are given by their xml id.
            The attribute 'group' may contain several xml ids, separated by commas.

        *   For a boolean field like 'module_XXX', ``execute`` triggers the immediate
            installation of the module named 'XXX' if the field has value ``True``.

        *   For a selection field like 'module_XXX' composed of 2 integers values ('0' and '1'),
            ``execute`` triggers the immediate installation of the module named 'XXX'
            if the field has the integer value ``1``.

        *   For a field with no specific prefix BUT an attribute 'config_parameter',
            ``execute``` will save its value in an ir.config.parameter (global setting for the
            database).

        *   For the other fields, the method ``execute`` invokes `set_values`.
            Override it to implement the effect of those fields.

        The method ``default_get`` retrieves values that reflect the current status of the
        fields like 'default_XXX', 'group_XXX', 'module_XXX' and config_XXX.
        It also invokes all methods with a name that starts with 'get_default_';
        such methods can be defined to provide current values for other fields.
    """
    _name = 'mc.res.config.settings'

    _description = 'Config Settings'

    @api.multi
    def copy(self, values):
        raise UserError(_("Cannot duplicate configuration!"), "")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        ret_val = super(McResConfigSettings, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

        can_install_modules = self.env['ir.module.module'].check_access_rights(
                                    'write', raise_exception=False)

        doc = etree.XML(ret_val['arch'])

        for field in ret_val['fields']:
            if not field.startswith("module_"):
                continue
            for node in doc.xpath("//field[@name='%s']" % field):
                if not can_install_modules:
                    node.set("readonly", "1")
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = True
                    node.set("modifiers", json.dumps(modifiers))

        ret_val['arch'] = etree.tostring(doc, encoding='unicode')
        return ret_val

    @api.multi
    def onchange_module(self, field_value, module_name):
        ModuleSudo = self.env['ir.module.module'].sudo()
        modules = ModuleSudo.search(
            [('name', '=', module_name.replace("module_", '')),
            ('state', 'in', ['to install', 'installed', 'to upgrade'])])

        if modules and not field_value:
            deps = modules.sudo().downstream_dependencies()
            dep_names = (deps | modules).mapped('shortdesc')
            message = '\n'.join(dep_names)
            return {
                'warning': {
                    'title': _('Warning!'),
                    'message': _('Disabling this option will also uninstall the following modules \n%s') % message,
                }
            }
        return {}

    def _register_hook(self):
        """ Add an onchange method for each module field. """
        def make_method(name):
            return lambda self: self.onchange_module(self[name], name)

        for name in self._fields:
            if name.startswith('module_'):
                method = make_method(name)
                self._onchange_methods[name].append(method)

    @api.model
    def _get_classified_fields(self):
        """ return a dictionary with the fields classified by category::

                {   'default': [('default_foo', 'model', 'foo'), ...],
                    'group':   [('group_bar', [browse_group], browse_implied_group), ...],
                    'module':  [('module_baz', browse_module), ...],
                    'config':  [('config_qux', 'my.parameter'), ...],
                    'other':   ['other_field', ...],
                }
        """
        IrModule = self.env['ir.module.module']
        Groups = self.env['res.groups']
        ref = self.env.ref

        defaults, groups, modules, configs, others = [], [], [], [], []
        for name, field in self._fields.items():
            if name.startswith('default_'):
                if not hasattr(field, 'default_model'):
                    raise Exception("Field %s without attribute 'default_model'" % field)
                defaults.append((name, field.default_model, name[8:]))
            elif name.startswith('group_'):
                if field.type not in ('boolean', 'selection'):
                    raise Exception("Field %s must have type 'boolean' or 'selection'" % field)
                if not hasattr(field, 'implied_group'):
                    raise Exception("Field %s without attribute 'implied_group'" % field)
                field_group_xmlids = getattr(field, 'group', 'base.group_user').split(',')
                field_groups = Groups.concat(*(ref(it) for it in field_group_xmlids))
                groups.append((name, field_groups, ref(field.implied_group)))
            elif name.startswith('module_'):
                if field.type not in ('boolean', 'selection'):
                    raise Exception("Field %s must have type 'boolean' or 'selection'" % field)
                module = IrModule.sudo().search([('name', '=', name[7:])], limit=1)
                modules.append((name, module))
            elif hasattr(field, 'config_parameter'):
                if field.type not in ('boolean', 'integer', 'float', 'char', 'selection', 'many2one'):
                    raise Exception("Field %s must have type 'boolean', 'integer', 'float', 'char', 'selection' or 'many2one'" % field)
                configs.append((name, field.config_parameter))
            else:
                others.append(name)

        return {'default': defaults, 'group': groups, 'module': modules, 'config': configs, 'other': others}

    def get_values(self):
        """
        Return values for the fields other that `default`, `group` and `module`
        """
        return {}

    @api.model
    def default_get(self, fields):
        IrDefault = self.env['ir.default']
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        classified = self._get_classified_fields()

        res = super(McResConfigSettings, self).default_get(fields)

        # defaults: take the corresponding default value they set
        for name, model, field in classified['default']:
            value = IrDefault.get(model, field)
            if value is not None:
                res[name] = value

        # groups: which groups are implied by the group Employee
        for name, groups, implied_group in classified['group']:
            res[name] = all(implied_group in group.implied_ids for group in groups)
            if self._fields[name].type == 'selection':
                res[name] = int(res[name])

        # modules: which modules are installed/to install
        for name, module in classified['module']:
            res[name] = module.state in ('installed', 'to install', 'to upgrade')
            if self._fields[name].type == 'selection':
                res[name] = int(res[name])

        # config: get & convert stored ir.config_parameter (or default)
        WARNING_MESSAGE = "Error when converting value %r of field %s for ir.config.parameter %r"
        for name, icp in classified['config']:
            field = self._fields[name]
            value = IrConfigParameter.get_param(icp, field.default(self) if field.default else False)
            if value is not False:
                if field.type == 'many2one':
                    try:
                        # Special case when value is the id of a deleted record, we do not want to
                        # block the settings screen
                        value = self.env[field.comodel_name].browse(int(value)).exists().id
                    except ValueError:
                        _logger.warning(WARNING_MESSAGE, value, field, icp)
                        value = False
                elif field.type == 'integer':
                    try:
                        value = int(value)
                    except ValueError:
                        _logger.warning(WARNING_MESSAGE, value, field, icp)
                        value = 0
                elif field.type == 'float':
                    try:
                        value = float(value)
                    except ValueError:
                        _logger.warning(WARNING_MESSAGE, value, field, icp)
                        value = 0.0
                elif field.type == 'boolean':
                    value = bool(value)
            res[name] = value

        # other fields: call the method 'get_values'
        # The other methods that start with `get_default_` are deprecated
        for method in dir(self):
            if method.startswith('get_default_'):
                _logger.warning(_('Methods that start with `get_default_` are deprecated. Override `get_values` instead(Method %s)') % method)
        res.update(self.get_values())

        return res

    def set_values(self):
        """
        Set values for the fields other that `default`, `group` and `module`
        """
        self = self.with_context(active_test=False)
        classified = self._get_classified_fields()

        # default values fields
        IrDefault = self.env['ir.default'].sudo()
        for name, model, field in classified['default']:
            if isinstance(self[name], models.BaseModel):
                if self._fields[name].type == 'many2one':
                    value = self[name].id
                else:
                    value = self[name].ids
            else:
                value = self[name]
            IrDefault.set(model, field, value)

        # group fields: modify group / implied groups
        current_settings = self.default_get(list(self.fields_get()))
        with self.env.norecompute():
            for name, groups, implied_group in classified['group']:
                if self[name] == current_settings[name]:
                    continue
                if self[name]:
                    groups.write({'implied_ids': [(4, implied_group.id)]})
                else:
                    groups.write({'implied_ids': [(3, implied_group.id)]})
                    implied_group.write({'users': [(3, user.id) for user in groups.mapped('users')]})
        self.recompute()

        # config fields: store ir.config_parameters
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        for name, icp in classified['config']:
            field = self._fields[name]
            value = self[name]
            if field.type == 'char':
                # storing developer keys as ir.config_parameter may lead to nasty
                # bugs when users leave spaces around them
                value = (value or "").strip() or False
            elif field.type in ('integer', 'float'):
                value = repr(value) if value else False
            elif field.type == 'many2one':
                # value is a (possibly empty) recordset
                value = value.id
            IrConfigParameter.set_param(icp, value)

        # other fields: execute method 'set_values'
        # Methods that start with `set_` are now deprecated
        for method in dir(self):
            if method.startswith('set_') and method is not 'set_values':
                _logger.warning(_('Methods that start with `set_` are deprecated. Override `set_values` instead (Method %s)') % method)

    @api.multi
    def execute(self):
        self.ensure_one()
        if not self.env.user._is_admin() and not self.env.user.has_group('base.group_system'):
            raise AccessError(_("Only administrators can change the settings"))

        self = self.with_context(active_test=False)
        classified = self._get_classified_fields()

        self.set_values()

        # module fields: install/uninstall the selected modules
        to_install = []
        to_uninstall_modules = self.env['ir.module.module']
        lm = len('module_')
        for name, module in classified['module']:
            if self[name]:
                to_install.append((name[lm:], module))
            else:
                if module and module.state in ('installed', 'to upgrade'):
                    to_uninstall_modules += module

        if to_uninstall_modules:
            to_uninstall_modules.button_immediate_uninstall()

        self._install_modules(to_install)

        if to_install or to_uninstall_modules:
            # After the uninstall/install calls, the registry and environments
            # are no longer valid. So we reset the environment.
            self.env.reset()
            self = self.env()[self._name]

        # pylint: disable=next-method-called
        config = self.env['res.config'].next() or {}
        if config.get('type') not in ('ir.actions.act_window_close',):
            return config

        # force client-side reload (update user menu and current view)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def cancel(self):
        # ignore the current record, and send the action to reopen the view
        actions = self.env['ir.actions.act_window'].search([('res_model', '=', self._name)], limit=1)
        if actions:
            return actions.read()[0]
        return {}

    @api.multi
    def name_get(self):
        """ Override name_get method to return an appropriate configuration wizard
        name, and not the generated name."""
        action = self.env['ir.actions.act_window'].search([('res_model', '=', self._name)], limit=1)
        name = action.name or self._name
        return [(record.id, name) for record in self]

    @api.model
    def get_option_path(self, menu_xml_id):
        """
        Fetch the path to a specified configuration view and the action id to access it.

        :param string menu_xml_id: the xml id of the menuitem where the view is located,
            structured as follows: module_name.menuitem_xml_id (e.g.: "sales_team.menu_sale_config")
        :return tuple:
            - t[0]: string: full path to the menuitem (e.g.: "Settings/Configuration/Sales")
            - t[1]: int or long: id of the menuitem's action
        """
        ir_ui_menu = self.env.ref(menu_xml_id)
        return (ir_ui_menu.complete_name, ir_ui_menu.action.id)

    @api.model
    def get_option_name(self, full_field_name):
        """
        Fetch the human readable name of a specified configuration option.

        :param string full_field_name: the full name of the field, structured as follows:
            model_name.field_name (e.g.: "sale.config.settings.fetchmail_lead")
        :return string: human readable name of the field (e.g.: "Create leads from incoming mails")
        """
        model_name, field_name = full_field_name.rsplit('.', 1)
        return self.env[model_name].fields_get([field_name])[field_name]['string']

    @api.model_cr_context
    def get_config_warning(self, msg):
        """
        Helper: return a Warning exception with the given message where the %(field:xxx)s
        and/or %(menu:yyy)s are replaced by the human readable field's name and/or menuitem's
        full path.

        Usage:
        ------
        Just include in your error message %(field:model_name.field_name)s to obtain the human
        readable field's name, and/or %(menu:module_name.menuitem_xml_id)s to obtain the menuitem's
        full path.

        Example of use:
        ---------------
        from odoo.addons.base.models.res_config import get_warning_config
        raise get_warning_config(cr, _("Error: this action is prohibited. You should check the field %(field:sale.config.settings.fetchmail_lead)s in %(menu:sales_team.menu_sale_config)s."), context=context)

        This will return an exception containing the following message:
            Error: this action is prohibited. You should check the field Create leads from incoming mails in Settings/Configuration/Sales.

        What if there is another substitution in the message already?
        -------------------------------------------------------------
        You could have a situation where the error message you want to upgrade already contains a substitution. Example:
            Cannot find any account journal of %s type for this company.\n\nYou can create one in the menu: \nConfiguration\Journals\Journals.
        What you want to do here is simply to replace the path by %menu:account.menu_account_config)s, and leave the rest alone.
        In order to do that, you can use the double percent (%%) to escape your new substitution, like so:
            Cannot find any account journal of %s type for this company.\n\nYou can create one in the %%(menu:account.menu_account_config)s.
        """
        self = self.sudo()

        # Process the message
        # 1/ find the menu and/or field references, put them in a list
        regex_path = r'%\(((?:menu|field):[a-z_\.]*)\)s'
        references = re.findall(regex_path, msg, flags=re.I)

        # 2/ fetch the menu and/or field replacement values (full path and
        #    human readable field's name) and the action_id if any
        values = {}
        action_id = None
        for item in references:
            ref_type, ref = item.split(':')
            if ref_type == 'menu':
                values[item], action_id = self.get_option_path(ref)
            elif ref_type == 'field':
                values[item] = self.get_option_name(ref)

        # 3/ substitute and return the result
        if (action_id):
            return RedirectWarning(msg % values, action_id, _('Go to the configuration panel'))
        return UserError(msg % values)


class McResConfigSettings(models.TransientModel):

    _inherit = 'mc.res.config.settings'

    group_multi_company = fields.Boolean("Manage multiple companies", implied_group='base.group_multi_company')
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    user_default_rights = fields.Boolean(
        "Default Access Rights",
        config_parameter='base_setup.default_user_rights',
        oldname='default_user_rights')
    external_email_server_default = fields.Boolean(
        "External Email Servers",
        config_parameter='base_setup.default_external_email_server',
        oldname='default_external_email_server')
    module_base_import = fields.Boolean("Allow users to import data from CSV/XLS/XLSX/ODS files")
    module_google_calendar = fields.Boolean(
        string='Allow the users to synchronize their calendar  with Google Calendar')
    module_google_drive = fields.Boolean("Attach Google documents to any record")
    module_google_spreadsheet = fields.Boolean("Google Spreadsheet")
    module_auth_oauth = fields.Boolean("Use external authentication providers (OAuth)")
    module_auth_ldap = fields.Boolean("LDAP Authentication")
    module_base_gengo = fields.Boolean("Translate Your Website with Gengo")
    module_inter_company_rules = fields.Boolean("Manage Inter Company")
    module_pad = fields.Boolean("Collaborative Pads")
    module_voip = fields.Boolean("Asterisk (VoIP)")
    module_web_unsplash = fields.Boolean("Unsplash Image Library")
    module_partner_autocomplete = fields.Boolean("Auto-populate company data")
    company_share_partner = fields.Boolean(string='Share partners to all companies',
        help="Share your partners to all companies defined in your instance.\n"
             " * Checked : Partners are visible for every companies, even if a company is defined on the partner.\n"
             " * Unchecked : Each company can see only its partner (partners where company is defined). Partners not related to a company are visible for all companies.")
    report_footer = fields.Text(related="company_id.report_footer", string='Custom Report Footer', help="Footer text displayed at the bottom of all reports.", readonly=False)
    group_multi_currency = fields.Boolean(string='Multi-Currencies',
            implied_group='base.group_multi_currency',
            help="Allows to work in a multi currency environment")
    paperformat_id = fields.Many2one(related="company_id.paperformat_id", string='Paper format', readonly=False)
    external_report_layout_id = fields.Many2one(related="company_id.external_report_layout_id", readonly=False)
    show_effect = fields.Boolean(string="Show Effect", config_parameter='base_setup.show_effect')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            company_share_partner=not self.env.ref('base.res_partner_rule').active,
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.ref('base.res_partner_rule').write({'active': not self.company_share_partner})

    @api.multi
    def open_company(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Company',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.company',
            'res_id': self.env.user.company_id.id,
            'target': 'current',
        }
    @api.multi
    def open_default_user(self):
        action = self.env.ref('base.action_res_users').read()[0]
        action['res_id'] = self.env.ref('base.default_user').id
        action['views'] = [[self.env.ref('base.view_users_form').id, 'form']]
        return action

    @api.model
    def _prepare_report_view_action(self, template):
        template_id = self.env.ref(template)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.ui.view',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': template_id.id,
        }

    @api.multi
    def edit_external_header(self):
        if not self.external_report_layout_id:
            return False
        return self._prepare_report_view_action(self.external_report_layout_id.key)

    @api.multi
    def change_report_template(self):
        self.ensure_one()
        template = self.env.ref('base.view_company_document_template_form')
        return {
            'name': _('Choose Your Document Layout'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.env.user.company_id.id,
            'res_model': 'res.company',
            'views': [(template.id, 'form')],
            'view_id': template.id,
            'target': 'new',
        }