odoo.define("ctimepicker.timepicker", function (require) {
  "use strict";

  var core = require("web.core");
  var datepicker = require("web.datepicker");
  var registry = require("web.field_registry");
  var basic_fields = require("web.basic_fields");
  var time = require("web.time");

  var FieldDate = basic_fields.FieldDate;
  var DateWidget = datepicker.DateWidget;
  var _lt = core._lt;

  var timepicker = DateWidget.extend({
    type_of_date: "char",
    init: function (parent, options) {
      this._super(
        parent,
        _.extend(
          {
            format: time.getLangTimeFormat(),
            buttons: {
              showToday: false,
              showClear: false,
              showClose: true,
            },
          },
          options || {}
        )
      );
    },

    getValue: function () {
      var value = this.get("value");
      try {
        return value && value.clone();
      } catch (e) {
        value = moment.utc(value, time.getLangTimeFormat());
        return value && value.clone();
      }
    },

    _formatClient: function (v) {
      return this._formatTime(v, null, { timezone: false });
    },

    _formatTime: function (value, field, options) {
      if (value === false) {
        return "";
      }
      value = moment(value, time.getLangTimeFormat());
      return value.format(time.getLangTimeFormat());
    },

    _parseClient: function (v) {
      return this._parseTime(v, null, { timezone: false });
    },

    _parseTime: function (value, field, options) {
      if (!value) {
        return false;
      }
      var timePattern = time.getLangTimeFormat();
      return moment.utc(value, timePattern);
    },
  });

  var ctimepicker = FieldDate.extend({
    description: _lt("Time"),
    tagName: "span",
    supportedFieldTypes: "char",

    init: function () {
      this._super.apply(this, arguments);
      if (this.value) {
        this.datepickerOptions.defaultDate = {};
      }
    },

    _getValue: function () {
      return this.datewidget.getValue().format(time.getLangTimeFormat());
    },

    _isSameValue: function (value) {
      if (value === false) {
        return this.value === false;
      }
      return false;
    },

    _makeDatePicker: function () {
      return new timepicker(this, this.datepickerOptions);
    },
  });

  registry.add("ctimepicker", ctimepicker);
});
