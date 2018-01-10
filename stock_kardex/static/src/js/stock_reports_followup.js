odoo.define('stock_kardex.stock_report_followup', function (require) {
'use strict';

var core = require('web.core');
var Pager = require('web.Pager');
var datepicker = require('web.datepicker');
var Dialog = require('web.Dialog');
var stock_report = require('stock_kardex.stock_report');

var QWeb = core.qweb;

var stock_report_followup = stock_report.extend({
    events: _.defaults({
        'click .changeTrust': 'change_trust',
        'click .js_change_date': 'display_exp_note_modal',
        'click .followup-email': 'send_followup_email',
        'click .followup-letter': 'print_pdf',
        "change *[name='blocked']": 'on_change_blocked',
    }, stock_report.prototype.events),
    init: function(parent, action) {
        this._super.apply(this, arguments);
        this.ignore_session = 'both';
    },
    parse_reports_informations: function(values) {
        this.map_partner_manager = values.map_partner_manager;
        return this._super(values);
    },
    render: function() {
        if (this.report_options.partners_to_show){
            this.renderPager();
            this.render_searchview();
        }
        this._super();
    },
    renderPager: function() {
        var self = this;
        var pager = new Pager(this, this.report_options.total_pager, this.report_options.pager, 1);
        pager.appendTo($('<div>')); // render the pager
        this.$pager = pager.$el;
        pager.on('pager_changed', this, function (state) {
            self.report_options.pager = state.current_min;
            self.reload();
        });
        return this.$pager;
    },
    render_searchview: function() {
        this.$searchview = $(QWeb.render("stockReports.followupProgressbar", {options: this.report_options}));
    },
    change_trust: function(e) {
        var partner_id = $(e.target).parents('span.dropdown').data("partner");
        var newTrust = $(e.target).data("new-trust");
        if (!newTrust) {
            newTrust = $(e.target).parents('a.changeTrust').data("new-trust");
        }
        var color = 'grey';
        switch(newTrust) {
            case 'good':
                color = 'green';
                break;
            case 'bad':
                color = 'red';
                break;
        }
    },
    display_done: function(e) {
        $(e.target).parents('.o_stock_reports_body').find("div.o_stock_reports_page").find(".alert.alert-info.alert-dismissible").remove();
        $(e.target).parents('.o_stock_reports_body').find('#action-buttons').addClass('o_stock_reports_followup_clicked');
        if ($(e.target).hasClass('btn-primary')){
            $(e.target).toggleClass('btn-primary btn-default');
        }
    },
    send_followup_email: function(e) {
        var self = this;
        var partner_id = $(e.target).data('partner');
        this.report_options['partner_id'] = partner_id;
        return this._rpc({
                model: this.report_model,
                method: 'send_email',
                args: [this.report_options],
            })
            .then(function (result) { // send the email server side
                self.display_done(e);
                $(e.target).parents("div.o_stock_reports_page").prepend(QWeb.render("emailSent")); // If all went well, notify the user
            });
    },
    print_pdf: function(e) {
        this.display_done(e);
    },
});
core.action_registry.add("stock_report_followup", stock_report_followup);
return stock_report_followup;
});
