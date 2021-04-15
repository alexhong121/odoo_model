odoo.define('mc_homepafe', function (require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var session = require("web.session");
    var qweb = core.qweb;
    var _t = core._t;
    var _lt = core._lt;

    var HomePage = AbstractAction.extend({
        template: 'home_page',
        start: function () {
            console.log(session)
            this._setBackgroundImage();
        },
        _setBackgroundImage: function () {
            var url = session.url('/web/image', {
                model: 'res.company',
                id: session.company_id,
                field: 'background_image',
            });
            this.$el.css({
                "background-size": "cover",
                "background-image": "url(" + url + ")"
            });
            if (session.muk_web_theme_background_blend_mode) {
                this.$('.o-app-name').css({
                    "mix-blend-mode": session.muk_web_theme_background_blend_mode,
                });
            }
        },
    });

    core.action_registry.add('mc_HomePage', HomePage);

    return HomePage;
});





