odoo.define('ws_tree.autofresh', function (require) {
        "use strict";

        window.onload=()=>{
            var d = new Date();
            if (true) {
                if ("WebSocket" in window) {
                    //建立ws连接
                    var host = "ws://" + window.location.hostname + ":9000";
                    var ws = new WebSocket(host);
                    ws.onmessage = function (event) {
                        var msg = event.data;
                        console.log('接收到数据...' + msg);
                    }
                }
            } else {
                alert("您的浏览器版本过低，请升级到最新版本!");
            }
        }
});
