odoo.define('hr_attendance_extend.gmaps', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var Widget = require('web.Widget');
    var core = require('web.core');
    var qweb = core.qweb;

    var gmaps = AbstractAction.extend({
        template: 'hr_attendance_extend_gmaps',

        init: function () {
            return this._super.apply(this, arguments);
        },
        start: function () {
            window.initMap = function () {
                var map = new google.maps.Map(document.getElementById('map'), {
                    center: {lat: -34.397, lng: 150.644},
                    zoom: 8
                });
            }
            var url = 'https://maps.googleapis.com/maps/api/js?key=AIzaSyCOwIYPWe7arnbx9zyyBYsVAGqwRr57SoE&callback=initMap';
            var jsapi = document.createElement('script');
            jsapi.charset = 'utf-8';
            jsapi.src = url;
            document.head.appendChild(jsapi);
        }
    })

    core.action_registry.add('hr_attendance_extend.gmaps', gmaps);
    return {
        gmaps: gmaps
    }
})