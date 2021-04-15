odoo.define('hr_attendance_extend.my_attendances', function (require) {
    "use strict";

    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');
    var QWeb = core.qweb;
    var _t = core._t;


    var MyOvertime = AbstractAction.extend({
        events: {
            "click .o_hr_attendance_sign_in_out_icon": _.debounce(function () {
                this.update_attendance();
            }, 200, true),
        },

        start: function () {
            var self = this;

            var def = this._rpc({
                model: 'hr.employee',
                method: 'search_read',
                args: [[['user_id', '=', this.getSession().uid]]],
            }).then(function (res) {
                    self.employee = res.length && res[0];
                    self.$el.html(QWeb.render("HrAttendanceOvertime", {widget: self}));
                });

            return $.when(def, this._super.apply(this, arguments));
        },

        update_attendance: function () {
            var self = this;
            this._rpc({
                model: 'hr.employee',
                method: 'attendance_overtime_manual',
                args: [[self.employee.id], 'hr_attendance_extend.hr_attendance_action_overtime'],
            })
                .then(function (result) {
                    if (result.action) {
                        self.do_action(result.action);
                    } else if (result.warning) {
                        self.do_warn(result.warning);
                    }
                });
        },
    });

    core.action_registry.add('hr_attendance_my_overtime', MyOvertime);

    return MyOvertime;
});
