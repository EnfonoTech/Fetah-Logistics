frappe.ui.form.DriverQuickEntryForm = class DriverQuickEntryForm extends frappe.ui.form.QuickEntryForm {
    constructor(doctype, after_insert, init_callback, doc, force) {
        super(doctype, after_insert, init_callback, doc, force);
    }

    render_dialog() {
        super.render_dialog();
        
        const dialog = this.dialog;
        const d = dialog.fields_dict;
        
        if (!d.naming_series) {
            return;
        }

        function apply_series() {
            const employee = dialog.get_value("employee");
            const transporter = dialog.get_value("transporter");
            
            if (employee) {
                dialog.set_value("naming_series", "HR-DRI-.YYYY.-");
                dialog.set_value("transporter", "");
            }
            
            if (transporter) {
                dialog.set_value("naming_series", "LG-DR-.#####");
                dialog.set_value("employee", "");
            }
        }

        ["employee", "transporter"].forEach(field => {
            if (!d[field]) return;
            
            d[field].$input.on("change", () => {
                apply_series();
            });
            
            d[field].$input.on("awesomplete-selectcomplete", () => {
                apply_series();
            });
        });
    }
};

// Override make_quick_entry to use custom QuickEntryForm for Driver
const original_make_quick_entry = frappe.ui.form.make_quick_entry;

frappe.ui.form.make_quick_entry = function(doctype, after_insert, init_callback, doc, force) {
    var trimmed_doctype = doctype.replace(/ /g, "");
    var controller_name = "QuickEntryForm";
    
    if (frappe.ui.form[trimmed_doctype + "QuickEntryForm"]) {
        controller_name = trimmed_doctype + "QuickEntryForm";
    }
    
    frappe.quick_entry = new frappe.ui.form[controller_name](
        doctype,
        after_insert,
        init_callback,
        doc,
        force
    );
    
    return frappe.quick_entry.setup();
};
