odoo.define('upwork_invoice_import.action_button', function (require) {
    "use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var _t = core._t;

    ListController.include({
        renderButtons: function($node) {
        this._super.apply(this, arguments);
           if (this.$buttons) {this.$buttons.find('.oe_action_button').click(this.proxy('action_def'));}
        },

        action_def: function () {
            var self = this
            var user = session.uid;
            rpc.query({
                model: 'upwork.invoice.fatturapa',
                method: 'update_electronic_invoice',
                args: [[]],
            }).then(function (e) {
                self.do_action({
                    type: 'ir.actions.client',
                    tag: 'reload',
                });
                window.location
            });
        },
    });
});