odoo.define('pf_top_invoice_bils.pf_dmy_date_field', function (require) {
"use strict";

var basic_fields = require('web.basic_fields');
var core = require('web.core');
var datepicker = require('web.datepicker');
var fieldRegistry = require('web.field_registry');

var _t = core._t;

var DMY_DATE_FORMAT = 'DD/MM/YYYY';
var DMY_DATE_FORMAT_NO_ZERO = 'D/M/YYYY';

function formatDmyDate(value) {
    if (value === false || isNaN(value)) {
        return "";
    }
    return value.format(DMY_DATE_FORMAT);
}

function parseDmyDate(value) {
    if (!value) {
        return false;
    }
    var date = moment.utc(value, [DMY_DATE_FORMAT, DMY_DATE_FORMAT_NO_ZERO, moment.ISO_8601], true);
    if (date.isValid() && date.year() >= 1000) {
        date.toJSON = function () {
            return this.clone().locale('en').format('YYYY-MM-DD');
        };
        return date;
    }
    throw new Error(_.str.sprintf(_t("'%s' is not a correct date"), value));
}

var PfDmyDatePicker = datepicker.DateWidget.extend({
    init: function (parent, options) {
        options = _.extend({}, options || {}, {
            format: DMY_DATE_FORMAT,
        });
        this._super(parent, options);
    },

    _formatClient: function (value) {
        return formatDmyDate(value);
    },

    _parseClient: function (value) {
        return parseDmyDate(value);
    },
});

var PfDmyDateField = basic_fields.FieldDate.extend({
    supportedFieldTypes: ['date'],

    init: function () {
        this._super.apply(this, arguments);
        this.datepickerOptions.format = DMY_DATE_FORMAT;
    },

    _formatValue: function (value) {
        return formatDmyDate(value);
    },

    _parseValue: function (value) {
        return parseDmyDate(value);
    },

    _makeDatePicker: function () {
        return new PfDmyDatePicker(this, this.datepickerOptions);
    },
});

fieldRegistry.add('pf_dmy_date', PfDmyDateField);

return PfDmyDateField;
});
