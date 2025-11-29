// Copyright (c) 2025, Fateh Logistics and contributors
// For license information, please see license.txt

// Note: Quick Entry form customization is in driver_quick_entry.js (loaded globally)
// This file only contains standard form event handlers

frappe.ui.form.on("Driver", {
    refresh: function(frm) {
        // Only show Process Allowance button for internal drivers (those with employee)
        // External drivers will create Purchase Invoice from Trip Details
        if (frm.doc.employee && frm.doc.allowance_balance > 0) {
            frm.add_custom_button(__("Process Allowance"), function() {
                frm.events.process_allowance(frm);
            });
        }
        
        // Add Update Allowances button only for internal drivers (those with employee)
        // External drivers don't track allowances
        if (frm.doc.name && frm.doc.employee) {
            frm.add_custom_button(__("Update Allowances from Trips"), function() {
                frappe.call({
                    method: "fateh_logistics.api.update_driver_allowances",
                    args: {
                        driver_name: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: r.message.message || "Allowances updated",
                                indicator: "green"
                            });
                            frm.reload_doc();
                        }
                    }
                });
            });
        }
    },
    
    transporter: function(frm) {
        // When transporter is selected (external driver), set naming series to LG-DR-.#####
        if (frm.doc.transporter) {
            if (frm.doc.naming_series !== "LG-DR-.#####") {
                frm.set_value("naming_series", "LG-DR-.#####");
            }
            if (frm.doc.employee) {
                setTimeout(function() {
                    frm.set_value("employee", "");
                }, 100);
            }
        }
    },
    
    employee: function(frm) {
        // When employee is selected (internal driver), set naming series to HR-DRI-.YYYY.-
        if (frm.doc.employee) {
            if (frm.doc.naming_series !== "HR-DRI-.YYYY.-") {
                frm.set_value("naming_series", "HR-DRI-.YYYY.-");
            }
            if (frm.doc.transporter) {
                setTimeout(function() {
                    frm.set_value("transporter", "");
                }, 100);
            }
        }
    },
    
    onload: function(frm) {
        // Set naming series on load based on existing values (only for new documents or if not set)
        if (frm.is_new() || !frm.doc.naming_series) {
            if (frm.doc.transporter && !frm.doc.employee) {
                frm.set_value("naming_series", "LG-DR-.#####");
            } else if (frm.doc.employee && !frm.doc.transporter) {
                frm.set_value("naming_series", "HR-DRI-.YYYY.-");
            }
        }
    },
    
    process_allowance: function(frm) {
        const balance = frm.doc.allowance_balance || (frm.doc.allowance || 0) - (frm.doc.allowance_taken || 0);
        
        if (balance <= 0) {
            frappe.msgprint(__("No allowance balance to process"));
            return;
        }
        
        const dialog = new frappe.ui.Dialog({
            title: __('Process Allowance - Create Additional Salary'),
            fields: [
                {
                    fieldname: "info",
                    fieldtype: "HTML",
                    options: `<div class="alert alert-info" style="margin-bottom: 15px;">
                        <strong>Available Balance: ${format_currency(balance)}</strong>
                    </div>`
                },
                {
                    fieldname: "amount",
                    fieldtype: "Currency",
                    label: "Amount to Process",
                    default: balance,
                    reqd: 1
                }
            ],
            primary_action_label: __('Create Additional Salary'),
            primary_action: function() {
                const amount = dialog.get_value("amount");
                if (amount > balance) {
                    frappe.msgprint(__("Amount cannot exceed balance"));
                    return;
                }
                if (amount <= 0) {
                    frappe.msgprint(__("Amount must be greater than zero"));
                    return;
                }
                
                frappe.call({
                    method: "fateh_logistics.api.process_driver_allowance",
                    args: {
                        driver_name: frm.doc.name,
                        amount: amount
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: "green"
                            });
                            dialog.hide();
                            frm.reload_doc();
                            
                            if (r.message.document) {
                                setTimeout(() => {
                                    frappe.set_route("Form", r.message.doctype, r.message.document);
                                }, 1000);
                            }
                        }
                    },
                    error: function(r) {
                        frappe.msgprint(r.message || __("Error processing allowance"));
                    }
                });
            }
        });
        dialog.show();
    }
});
