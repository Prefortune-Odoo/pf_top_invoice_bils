/** @odoo-module **/

import { formatDate } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";
import { DateField } from "@web/views/fields/date/date_field";

const DMY_DATE_FORMAT = "dd/MM/yyyy";

export class PfDmyDateField extends DateField {
    get formattedValue() {
        return this.props.value ? formatDate(this.props.value, { format: DMY_DATE_FORMAT }) : "";
    }
}

PfDmyDateField.template = "web.DateField";
PfDmyDateField.displayName = DateField.displayName;
PfDmyDateField.supportedTypes = ["date"];
PfDmyDateField.extractProps = (params) => {
    const props = DateField.extractProps(params);
    return {
        ...props,
        pickerOptions: {
            ...(props.pickerOptions || {}),
            format: DMY_DATE_FORMAT,
        },
    };
};

registry.category("fields").add("pf_dmy_date", PfDmyDateField);
