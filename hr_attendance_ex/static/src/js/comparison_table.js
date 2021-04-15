odoo.define('mc.vacation_days_comparison_table', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;
    var _lt = core._lt;

    var ComparisonPage = AbstractAction.extend({
        events: {
            'click #update_btn': '_onClick',
        },

        init: function (parent, data) {
            this.updateDate = 0;
            this.data = [];
            return this._super.apply(this, arguments);
        },
        willStart: function () {
            return $.when(this._super.apply(this, arguments), this._fetchData());
        },
        start: function () {
            this.$el.empty();
            this.updateDate = this.data[0]['write_date'].substr(0,10);
            var doc = qweb.render('vacation_days_comparison', {widget: this});
            this.$el.append(doc);
        },
        _fetchData: function () {
            var self = this;
            return this._rpc({
                model: 'vacation.days.comparison',
                method: 'get_comparison_table',
                kwargs: {
                    domain: []
                }
            }).then(function (result) {
                self.data = result;
                return self.data
            });

        },
        _onClick: function () {
            var self = this;
            this._rpc({
                model: 'vacation.days.comparison',
                method: 'update_comparison_table',
                kwargs: {
                    domain: []
                }
            }).then(function (result) {
                self.data = result;
                self.$('#update_table').empty()
                var doc = qweb.render('comparison_table', {widget: self});
                self.$('#update_table').append(doc);
                self.updateDate = self.data[0]['write_date'].substr(0,10);
                self.$('.val').text(self.updateDate);
            });


        },
    });

    core.action_registry.add('mc_vacation_days_comparison_table', ComparisonPage);

    return {ComparisonPage: ComparisonPage};

});