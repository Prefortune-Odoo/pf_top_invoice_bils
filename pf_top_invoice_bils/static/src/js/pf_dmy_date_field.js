/** @odoo-module **/

import { onWillRender, useState } from "@odoo/owl";
import { useDateTimePicker } from "@web/core/datetime/datetime_hook";
import { areDatesEqual } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";
import { formatDate } from "@web/views/fields/formatters";
import { DateTimeField, dateField } from "@web/views/fields/datetime/datetime_field";

const DMY_DATE_FORMAT = "dd/MM/yyyy";

export class PfDmyDateField extends DateTimeField {
    static template = "web.DateTimeField";

    setup() {
        const getPickerProps = () => {
            const value = this.getRecordValue();
            const pickerProps = {
                value,
                type: this.field.type,
                range: this.isRange(value),
            };
            if (this.props.maxDate) {
                pickerProps.maxDate = this.parseLimitDate(this.props.maxDate);
            }
            if (this.props.minDate) {
                pickerProps.minDate = this.parseLimitDate(this.props.minDate);
            }
            if (!isNaN(this.props.rounding)) {
                pickerProps.rounding = this.props.rounding;
            } else if (!this.props.showSeconds) {
                pickerProps.rounding = 0;
            }
            if (this.props.maxPrecision) {
                pickerProps.maxPrecision = this.props.maxPrecision;
            }
            if (this.props.minPrecision) {
                pickerProps.minPrecision = this.props.minPrecision;
            }
            return pickerProps;
        };

        const dateTimePicker = useDateTimePicker({
            target: "root",
            showSeconds: this.props.showSeconds,
            condensed: this.props.condensed,
            format: DMY_DATE_FORMAT,
            get pickerProps() {
                return getPickerProps();
            },
            onChange: () => {
                this.state.range = this.isRange(this.state.value);
            },
            onApply: async () => {
                const toUpdate = {};
                if (Array.isArray(this.state.value)) {
                    [toUpdate[this.startDateField], toUpdate[this.endDateField]] = this.state.value;
                } else {
                    toUpdate[this.props.name] = this.state.value;
                }

                for (const fieldName in toUpdate) {
                    if (areDatesEqual(toUpdate[fieldName], this.props.record.data[fieldName])) {
                        delete toUpdate[fieldName];
                    }
                }

                if (Object.keys(toUpdate).length) {
                    await this.props.record.update(toUpdate);
                }
            },
        });

        this.state = useState(dateTimePicker.state);
        this.openPicker = dateTimePicker.open;

        onWillRender(() => this.triggerIsDirty());
    }

    getFormattedValue(valueIndex) {
        const value = this.values[valueIndex];
        return value ? formatDate(value, { condensed: this.props.condensed, format: DMY_DATE_FORMAT }) : "";
    }
}

export const pfDmyDateField = {
    ...dateField,
    component: PfDmyDateField,  
};

registry.category("fields").add("pf_dmy_date", pfDmyDateField);
