frappe.ui.form.VehicleQuickEntryForm = class VehicleQuickEntryForm extends frappe.ui.form.QuickEntryForm {
    constructor(doctype, after_insert, init_callback, doc, force) {
        super(doctype, after_insert, init_callback, doc, force);
    }

    render_dialog() {
        super.render_dialog();
        
        const dialog = this.dialog;
        const d = dialog.fields_dict;
        
        if (!d.custom_is_external) {
            return;
        }

        function toggle_requirements() {
            const is_external = dialog.get_value("custom_is_external") === "External";
            const fields_to_make_optional = ["make", "model", "last_odometer", "fuel_type", "uom"];
            
            if (is_external) {
                // Make license_plate mandatory
                if (d.license_plate) {
                    dialog.set_df_property("license_plate", "reqd", 1);
                }
                
                // Make all other fields optional
                fields_to_make_optional.forEach(function(fieldname) {
                    if (d[fieldname]) {
                        dialog.set_df_property(fieldname, "reqd", 0);
                    }
                });
            } else {
                // Internal vehicle - restore default requirements
                dialog.set_df_property("license_plate", "reqd", 1);
                dialog.set_df_property("make", "reqd", 1);
                dialog.set_df_property("model", "reqd", 1);
                dialog.set_df_property("last_odometer", "reqd", 1);
                dialog.set_df_property("fuel_type", "reqd", 1);
                dialog.set_df_property("uom", "reqd", 1);
            }
            
            dialog.refresh_dependency();
        }

        // Initial setup
        setTimeout(function() {
            toggle_requirements();
        }, 200);

        // Attach change event to custom_is_external field
        if (d.custom_is_external && d.custom_is_external.$input) {
            d.custom_is_external.$input.on("change", function() {
                toggle_requirements();
            });
            
            d.custom_is_external.$input.on("awesomplete-selectcomplete", function() {
                setTimeout(function() {
                    toggle_requirements();
                }, 100);
            });
        }
    }
};

