odoo.define('saara_spaces_models.readonly_mobile', ['@web/legacy/js/public/public_widget'], function (require) {
    "use strict";

    var publicWidget = require('@web/legacy/js/public/public_widget');

    publicWidget.registry.ReadonlyMobileField = publicWidget.Widget.extend({
        selector: "input[name='mobile']", // Targeting the input field
        start: function () {
            this._super.apply(this, arguments);
            this.$el.on('input', function () {
                if (!this.value.startsWith('+91')) {
                    this.value = '+91';
                }
            });
        },
    });
});