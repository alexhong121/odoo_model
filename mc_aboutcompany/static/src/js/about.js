odoo.define('mc.about', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;
    var _lt = core._lt;

    var AboutPage = AbstractAction.extend({
       init: function (parent, data) {
            this._super.apply(this, arguments);
            return this.data
        },
        willStart: function () {
            var colorDataDef = this._fetchData()
            return $.when(this._super.apply(this, arguments), colorDataDef);
        },
        start: function () {
            var pills = qweb.render('about_page', {widget: this});
            this.$el.append(pills);
        },
        _fetchData: function () {
            var self = this;
            return this._rpc({
                model: 'ir.module.module',
                method: 'get_ir_module_module_data',
                kwargs: {
                    domain: ['&', ['state', '=', 'installed'], ['application', '=', 't']]
                }
            }).then(function (result) {
                self.data = result;
                return self.data
            });
        },
    });

    core.action_registry.add('mc_AboutPage', AboutPage);

    return {AboutPage: AboutPage};

});