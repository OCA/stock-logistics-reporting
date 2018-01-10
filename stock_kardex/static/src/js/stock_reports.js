odoo.define('stock_kardex.stock_report', function (require) {
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');
var ControlPanelMixin = require('web.ControlPanelMixin');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var crash_manager = require('web.crash_manager');
var ActionManager = require('web.ActionManager');
var datepicker = require('web.datepicker');
var session = require('web.session');
var field_utils = require('web.field_utils');

var QWeb = core.qweb;
var _t = core._t;


var stockReportsWidget = Widget.extend(ControlPanelMixin, {

    events: {
        'click .js_stock_report_foldable': 'fold_unfold',
        'click [action]': 'trigger_action',
    },

    init: function(parent, action) {
        this.actionManager = parent;
        this.report_model = action.context.model;
        if (this.report_model === undefined) {
            this.report_model = 'stock.report';
        }
        this.stock_kardex_id = false;
        if (action.context.id) {
            this.stock_kardex_id = action.context.id;
        }
        this.odoo_context = action.context;
        this.report_options = action.options || false;
        this.ignore_session = action.ignore_session;
        if ((action.ignore_session === 'read' || action.ignore_session === 'both') !== true) {
            var persist_key = 'report:'+this.report_model+':'+this.stock_kardex_id+':'+session.company_id;
            this.report_options = JSON.parse(sessionStorage.getItem(persist_key)) || this.report_options;
        }
        return this._super.apply(this, arguments);
    },
    start: function() {
        var self = this;
        var extra_info = this._rpc({
                model: self.report_model,
                method: 'get_report_informations',
                args: [self.stock_kardex_id, self.report_options],
                context: self.odoo_context,
            })
            .then(function(result){
                return self.parse_reports_informations(result);
            });
        return $.when(extra_info, this._super.apply(this, arguments)).then(function() {
            self.render();
        });
    },
    parse_reports_informations: function(values) {
        this.report_options = values.options;
        this.odoo_context = values.context;
        this.report_manager_id = values.report_manager_id;
        this.footnotes = values.footnotes;
        this.buttons = values.buttons;

        this.main_html = values.main_html;
        this.$searchview_buttons = $(values.searchview_html);
        this.persist_options();
    },
    persist_options: function() {
        if ((this.ignore_session === 'write' || this.ignore_session === 'both') !== true) {
            var persist_key = 'report:'+this.report_model+':'+this.stock_kardex_id+':'+session.company_id;
            sessionStorage.setItem(persist_key, JSON.stringify(this.report_options));
        }
    },
    // We need this method to rerender the control panel when going back in the breadcrumb
    do_show: function() {
        this._super.apply(this, arguments);
        this.update_cp();
    },
    // Updates the control panel and render the elements that have yet to be rendered
    update_cp: function() {
        if (!this.$buttons) {
            this.renderButtons();
        }
        var status = {
            breadcrumbs: this.actionManager.get_breadcrumbs(),
            cp_content: {$buttons: this.$buttons, $searchview_buttons: this.$searchview_buttons, $pager: this.$pager, $searchview: this.$searchview},
        };
        return this.update_control_panel(status, {clear: true});
    },
    reload: function() {
        var self = this;
        return this._rpc({
                model: this.report_model,
                method: 'get_report_informations',
                args: [self.stock_kardex_id, self.report_options],
                context: self.odoo_context,
            })
            .then(function(result){
                self.parse_reports_informations(result);
                return self.render();
            });
    },
    render: function() {
        this.render_template();
        this.render_footnotes();
        this.render_searchview_buttons();
        this.update_cp();
    },
    render_template: function() {
        this.$el.html(this.main_html);
    },
    render_searchview_buttons: function() {
        var self = this;
        // bind searchview buttons/filter to the correct actions
        var $datetimepickers = this.$searchview_buttons.find('.js_stock_reports_datetimepicker');
        var options = { // Set the options for the datetimepickers
            locale : moment.locale(),
            format : 'L',
            icons: {
                date: "fa fa-calendar",
            },
        };
        // attach datepicker
        $datetimepickers.each(function () {
            $(this).datetimepicker(options);
            var dt = new datepicker.DateWidget(options);
            dt.replace($(this));
            dt.$el.find('input').attr('name', $(this).find('input').attr('name'));
            if($(this).data('default-value')) { // Set its default value if there is one
                dt.setValue(moment($(this).data('default-value')));
            }
        });
        // format date that needs to be show in user lang
        _.each(this.$searchview_buttons.find('.js_format_date'), function(dt) {
            var date_value = $(dt).html();
            $(dt).html((new moment(date_value)).format('ll'));
        });
        // fold all menu
        this.$searchview_buttons.find('.js_foldable_trigger').click(function (event) {
            $(this).toggleClass('o_closed_menu o_open_menu');
            self.$searchview_buttons.find('.o_foldable_menu[data-filter="'+$(this).data('filter')+'"]').toggleClass('o_closed_menu o_open_menu');
        });
        // render filter (add selected class to the options that are selected)
        _.each(self.report_options, function(k) {
            if (k!== null && k.filter !== undefined) {
                self.$searchview_buttons.find('[data-filter="'+k.filter+'"]').addClass('selected');
            }
        });
        // click event
        this.$searchview_buttons.find('.js_stock_report_date_filter').click(function (event) {
            self.report_options.date.filter = $(this).data('filter');
            var error = false;
            if ($(this).data('filter') === 'custom') {
                var date_from = self.$searchview_buttons.find('.o_datepicker_input[name="date_from"]');
                var date_to = self.$searchview_buttons.find('.o_datepicker_input[name="date_to"]');
                if (date_from.length > 0){
                    error = date_from.val() === "" || date_to.val() === "";
                    self.report_options.date.date_from = field_utils.parse.date(date_from.val());
                    self.report_options.date.date_to = field_utils.parse.date(date_to.val());
                }
                else {
                    error = date_to.val() === "";
                    self.report_options.date.date = field_utils.parse.date(date_to.val());
                }
            }
            if (error) {
                crash_manager.show_warning({data: {message: _t('Date cannot be empty')}});
            } else {
                self.reload();
            }
        });
        // analytic filter
        this.$searchview_buttons.find('.js_stock_reports_product_auto_complete').select2();
        if (self.report_options.product) {
            self.$searchview_buttons.find('[data-filter="product_ids"]').select2("val", self.report_options.product_ids);
            self.$searchview_buttons.find('[data-filter="analytic_tags"]').select2("val", self.report_options.analytic_tags);
        }
        this.$searchview_buttons.find('.js_stock_reports_product_auto_complete').on('change', function(){
            self.report_options.product_ids = self.$searchview_buttons.find('[data-filter="product_ids"]').val();
            self.report_options.analytic_tags = self.$searchview_buttons.find('[data-filter="analytic_tags"]').val();
            return self.reload().then(function(){
                self.$searchview_buttons.find('.stock_product_filter').click();
            })
        });
    },
    format_date: function(moment_date) {
        var date_format = 'YYYY-MM-DD';
        return moment_date.format(date_format);
    },
    renderButtons: function() {
        var self = this;
        this.$buttons = $(QWeb.render("stockReports.buttons", {buttons: this.buttons}));
        // bind actions
        _.each(this.$buttons.siblings('button'), function(el) {
            $(el).click(function() {
                return self._rpc({
                        model: self.report_model,
                        method: $(el).attr('action'),
                        args: [self.stock_kardex_id, self.report_options],
                        context: self.odoo_context,
                    })
                    .then(function(result){
                        return self.do_action(result);
                    });
            });
        });
        return this.$buttons;
    },
    render_footnotes: function() {
        var self = this;
        // First assign number based on visible lines
        var $dom_footnotes = self.$el.find('.js_stock_report_line_footnote:not(.folded)');
        $dom_footnotes.html('');
        var number = 1;
        var footnote_to_render = [];
        _.each($dom_footnotes, function(el) {
            var line_id = $(el).data('id');
            var footnote = _.filter(self.footnotes, function(footnote) {return ''+footnote.line === ''+line_id;});
            if (footnote.length !== 0) {
                $(el).html('<sup><b class="o_stock_reports_footnote_sup"><a href="#footnote'+number+'">'+number+'</a></b></sup>');
                footnote[0].number = number;
                number += 1;
                footnote_to_render.push(footnote[0]);
            }
        });
        // Render footnote template
        return this._rpc({
                model: this.report_model,
                method: 'get_html_footnotes',
                args: [self.stock_kardex_id, footnote_to_render],
                context: self.odoo_context,
            })
            .then(function(result){
                return self.$el.find('.js_stock_report_footnotes').html(result);
            });
    },
    fold_unfold: function(e) {
        var self = this;
        if ($(e.target).hasClass('caret') || $(e.target).parents('.o_stock_reports_footnote_sup').length > 0){return;}
        e.stopPropagation();
        e.preventDefault();
        var line = $(e.target).parents('td');
        if (line.length === 0) {line = $(e.target);}
        var method = line.data('unfolded') === 'True' ? this.fold(line) : this.unfold(line);
        $.when(method).then(function() {
            self.render_footnotes();
            self.persist_options();
        });
    },
    fold: function(line) {
        var self = this;
        var line_id = line.data('id');
        line.find('.fa-caret-down').toggleClass('fa-caret-right fa-caret-down');
        line.toggleClass('folded');
        var $lines_to_hide = this.$el.find('tr[data-parent-id="'+line_id+'"]');
        var index = self.report_options.unfolded_lines.indexOf(line_id);
        if (index > -1) {
            self.report_options.unfolded_lines.splice(index, 1);
        }
        if ($lines_to_hide.length > 0) {
            line.data('unfolded', 'False');
            $lines_to_hide.find('.js_stock_report_line_footnote').addClass('folded');
            $lines_to_hide.hide();
            _.each($lines_to_hide, function(el){
                var child = $(el).find('[data-id]:first');
                if (child) {
                    self.fold(child);
                }
            })
        }
        return false;
    },
    unfold: function(line) {
        var self = this;
        var line_id = line.data('id');
        line.toggleClass('folded');
        self.report_options.unfolded_lines.push(line_id);
        var $lines_in_dom = this.$el.find('tr[data-parent-id="'+line_id+'"]');
        if ($lines_in_dom.length > 0) {
            $lines_in_dom.find('.js_stock_report_line_footnote').removeClass('folded');
            $lines_in_dom.show();
            line.find('.fa-caret-right').toggleClass('fa-caret-right fa-caret-down');
            line.data('unfolded', 'True');
            return true;
        }
        else {
            return this._rpc({
                    model: this.report_model,
                    method: 'get_html',
                    args: [self.stock_kardex_id, self.report_options, line.data('id')],
                    context: self.odoo_context,
                })
                .then(function(result){
                    $(line).parent('tr').replaceWith(result);
                });
        }
    },
    unfold_all: function(bool) {
        var self = this;
        var lines = this.$el.find('.js_stock_report_foldable');
        self.report_options.unfolded_lines = [];
        if (bool) {
            _.each(lines, function(el) {
                self.report_options.unfolded_lines.push($(el).data('id'));
            });
        }
    },
    trigger_action: function(e) {
        e.stopPropagation();
        var self = this;
        var action = $(e.target).attr('action');
        var id = $(e.target).parents('td').data('id');
        var params = $(e.target).data();
        if (action) {
            return this._rpc({
                    model: this.report_model,
                    method: action,
                    args: [this.stock_kardex_id, this.report_options, params],
                    context: this.odoo_context,
                })
                .then(function(result){
                    return self.do_action(result);
                });
        }
    },
});

ActionManager.include({
    ir_actions_stock_report_download: function(action, options) {
        var self = this;
        var c = crash_manager;
        return $.Deferred(function (d) {
            self.getSession().get_file({
                url: '/stock_kardex',
                data: action.data,
                complete: framework.unblockUI,
                success: function(){
                    if (!self.dialog) {
                        options.on_close();
                    }
                    self.dialog_stop();
                    d.resolve();
                },
                error: function () {
                    c.rpc_error.apply(c, arguments);
                    d.reject();
                }
            });
        });
    }
});

core.action_registry.add('stock_report', stockReportsWidget);
return stockReportsWidget;
});
