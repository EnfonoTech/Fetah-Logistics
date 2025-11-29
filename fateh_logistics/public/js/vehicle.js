// Copyright (c) 2025, siva@enfono.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vehicle", {
    refresh: function (frm) {
        frm.events.toggle_field_requirements(frm);
    },
    
    custom_is_external: function(frm) {
        frm.events.toggle_field_requirements(frm);
    },
    
    onload: function(frm) {
        frm.events.toggle_field_requirements(frm);
    },
    
    toggle_field_requirements: function(frm) {
        const is_external = frm.doc.custom_is_external === "External";
        
        // Fields that should be optional when External is selected (except license_plate)
        const fields_to_make_optional = ["make", "model", "last_odometer", "fuel_type", "uom"];
        
        if (is_external) {
            // Make license_plate mandatory
            frm.set_df_property("license_plate", "reqd", 1);
            
            // Make all other fields optional
            fields_to_make_optional.forEach(function(fieldname) {
                if (frm.fields_dict[fieldname]) {
                    frm.set_df_property(fieldname, "reqd", 0);
                }
            });
        } else {
            // Internal vehicle - restore default requirements
            frm.set_df_property("license_plate", "reqd", 1);
            
            // Restore default mandatory fields
            frm.set_df_property("make", "reqd", 1);
            frm.set_df_property("model", "reqd", 1);
            frm.set_df_property("last_odometer", "reqd", 1);
            frm.set_df_property("fuel_type", "reqd", 1);
            frm.set_df_property("uom", "reqd", 1);
        }
        
        frm.refresh_fields();
    }
});
