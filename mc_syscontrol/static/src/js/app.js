odoo.define('web_window_title', function (require) {
    "use strict";
    
    var WebClient = require('web.WebClient');
    WebClient.include({
        init: function() {
            this._super.apply(this, arguments);
            this.set('title_part', {"zopenerp":document.title});
        }
    });

    // window.onload=()=>{
    //     function shield(){
    //         let body=document.getElementsByTagName('body')
    //         let div = document.createElement("div");
    //         div.setAttribute('id','stop')
    //         body[0].appendChild(div);
    //     }
    //     /*判斷手機系統是Android還是IOS*/
    //     if(navigator.userAgent.match(/android/i)){
    //         //如果是Android的話
    //         shield()
    //     }else if(navigator.userAgent.match(/(iphone|ipad|ipod);?/i)){
    //         //如果是IOS的話
    //         shield()
    //     }else{
    //         //其他，電腦的瀏覽器，可以
    //         console.log("正在shield執行中！")
    //     }
    // }
});





