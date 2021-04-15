odoo.define('hr_attendance_extend.amap', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var Widget = require('web.Widget');
    var core = require('web.core');
    var qweb = core.qweb;

    var amap = AbstractAction.extend({
        events: {
            'click #openSelectRange': '_openSettingRangeSelect',
            'click .map_rangeDistance':'_settingRangeDistance'
        },
        init: function () {
            this.distance=300
            this.markers=[]
            this.positions=[]
            this.circleMarkers=[]
            this.centerPoint={}
            return this._super.apply(this, arguments);
        },
        start: function () {
            this.$el.empty();
            this.$el.addClass("template")
            var doc = qweb.render('hr_attendance_extend_setDistance', {widget: this});
            this.$el.append(doc);
            this.on_start();

        },
        on_start:function(){
            if(typeof AMap =="undefined")
                window.AMapinit=this.on_ready
                var url = 'https://webapi.amap.com/maps?v=1.4.15&key=838f9727e061f2d8bc87bdd0042b8921&callback=AMapinit';
                var jsapi = document.createElement('script');
                jsapi.charset = 'utf-8';
                jsapi.src = url;
                document.head.appendChild(jsapi);
        },
        on_ready:function(){
                //創建地圖物件
                var map = new AMap.Map('container', {
                    zoom: 14,
                    resizeEnable: true,
                    animateEnable:false,
                    zoomEnable:true
                });
                this.centerPoint = map.getCenter();
                this.positions.push([this.centerPoint.Q, this.centerPoint.P])
                var marker = new AMap.Marker({
                    position: this.positions[0],   // 经纬度对象，也可以是经纬度构成的一维数组[116.39, 39.9]
                });

                this.markers.push(marker)
                map.add(marker);

                var circleMarker=new AMap.Circle({
                    center:this.positions[0],
                    radius:this.distance,
                    strokeOpacity:0.6,
                    fillOpacity:0.5
                })
                this.circleMarkers.push(circleMarker)
                map.add(circleMarker);

                map.on('dragging', function (self) {
                    for (let index = 0; index < self.markers.length; index++) {
                        self.markers[index].setMap(null)
                        self.circleMarkers[index].setMap(null)
                    }

                    self.centerPoint = map.getCenter();
                    self.positions.push([self.centerPoint.Q, self.centerPoint.P])

                    var marker = new AMap.Marker({
                        position: [self.centerPoint.Q, self.centerPoint.P],   // 经纬度对象，也可以是经纬度构成的一维数组[116.39, 39.9]
                    });
                    var circleMarker=new AMap.Circle({
                        center:[self.centerPoint.Q, self.centerPoint.P],
                        radius:self.distance,
                        strokeOpacity:0.6,
                        fillOpacity:0.5
                    })

                    self.markers.push(marker)
                    map.add(marker)
                    self.circleMarkers.push(circleMarker)
                    map.add(circleMarker)
                    console.log('Lng: ' + self.centerPoint.Q + ' , ' + 'Lat: ' + self.centerPoint.P)

                }.bind(this,this))
        },
        _openSettingRangeSelect:function (event) {
            event.preventDefault();
            this.$(".map_table_container").toggleClass("map_active")
        },
        _settingRangeDistance:function (event) {
            event.preventDefault();
            this.distance=event.target.getAttribute('value')
            this.$(".map_table_container").toggleClass("map_active")
            this.$("#map_distance_text").text(this.distance+'米')
            this.on_ready()
        }
    })

    core.action_registry.add('hr_attendance_extend.amap', amap);
    return {
        amap: amap
    }
})