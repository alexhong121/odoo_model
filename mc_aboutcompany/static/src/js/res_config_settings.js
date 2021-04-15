odoo.define('mc_aboutcompany.settings',function (require) {

    var settingsRenderer=require('base.settings').Renderer

    settingsRenderer.include({
        _getAppIconUrl: function (module) {
            switch (module) {
                case "general_settings":
                    return module ="/base/static/description/settings.png"
                case "mc_aboutcompany":
                    return module ="/mc_aboutcompany/static/description/settings.png"
                default:
                    return module = "/"+module+"/static/description/icon.png";
            }
        }
    })

})