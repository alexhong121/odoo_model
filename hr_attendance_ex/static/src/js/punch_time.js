odoo.define('hr_attendance_extend.punch_time', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var Widget = require('web.Widget');
    var core = require('web.core');
    var qweb = core.qweb;
    var Amap= require('hr_attendance_extend.amap');

    var punchTime = AbstractAction.extend({
        template: 'hr_attendance_extend_punch_time',

        init: function () {
            return this._super.apply(this, arguments);
        },
        start: function () {
            // var contents =this.$("div.content")
            // var timeText=this.$("span.cus_button_text")
            // var timeButton=this.$("button.cus-button")
            // this.$("button.mdc-tab").on('click',function () {
            //     var page=this.getAttribute('page')
            //     contents.attr("class",contents.attr("class").replace(" active", ""))
            //     document.getElementById(page).className += " active";
            // })
            // var self=this
            // console.log(self.$(".cus_button_text"))
            // timeButton.on('click',function () {
            //     var currentTime=this.getElementsByClassName('cus_button_text')[0].innerHTML
            //     alert(currentTime)
            // })
            //
            // this._showTime(timeText)
            var amap=new Amap.amap()
            amap.on_start()
            this._super.apply(this, arguments);
        },
        // _showTime:function (timeText) {
        //       var dateTime=new Date();
        //       var time=dateTime.getHours()+':'+dateTime.getMinutes()+':'+dateTime.getSeconds()
        //         timeText.html(time)
        //       setTimeout(()=>this._showTime(timeText),1000)
        // },
        // _Geolocation:function () {
        //     if (navigator.geolocation) {
        //             navigator.geolocation.getCurrentPosition(this._showPosition);
        //           } else {
        //             console.log("Geolocation is not supported by this browser.");
        //           }
        //
        // },
        // _showPosition:function (position) {
        //     this.currentPosition =  {
        //             Lng:position.coords.longitude,
        //             Lat:position.coords.latitude
        //           }
        // }
    })

    core.action_registry.add('hr_attendance_extend.punch_time', punchTime);

    return {
        punchTime: punchTime
    }
})