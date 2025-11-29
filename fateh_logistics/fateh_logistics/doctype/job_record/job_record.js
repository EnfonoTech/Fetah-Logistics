// Copyright (c) 2025, siva@enfono.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Record", {
    onload: function (frm) {
        frm.events.load_quotation(frm);
        
        // Set query filter for driver field based on driver_type (row-specific)
        // This is set once and will dynamically read driver_type from the row
        frm.set_query('driver', 'job_assignment', function(doc, cdt, cdn) {
            const row = locals[cdt][cdn];
            
            if (row.driver_type === 'Own') {
                // Own drivers: employee field must be set (not null and not empty)
                return {
                    query: 'fateh_logistics.api.get_drivers_by_type',
                    filters: {
                        driver_type: 'Own'
                    }
                };
            } else if (row.driver_type === 'External') {
                // External drivers: employee field must be empty or null
                return {
                    query: 'fateh_logistics.api.get_drivers_by_type',
                    filters: {
                        driver_type: 'External'
                    }
                };
            }
            // If no driver_type selected, show all drivers
            return {};
        });

        // Set query filter for vehicle field based on driver_type (row-specific)
        frm.set_query('vehicle', 'job_assignment', function(doc, cdt, cdn) {
            const row = locals[cdt][cdn];
            
            if (row.driver_type === 'Own') {
                // Own drivers: show only internal vehicles
                return {
                    filters: {
                        custom_is_external: 'Internal'
                    }
                };
            } else if (row.driver_type === 'External') {
                // External drivers: show only external vehicles
                return {
                    filters: {
                        custom_is_external: 'External'
                    }
                };
            }
            // If no driver_type selected, show all vehicles
            return {};
        });
    },
    customer: function (frm) {
        if (frm.is_new() && frm.doc.customer) {
            frm.add_custom_button(__('Get Items from Quotation'), () => {
                frappe.call({
                    method: 'fateh_logistics.api.get_quotations_for_customer',
                    args: {
                        customer: frm.doc.customer
                    },
                    callback: function (r) {
                        const quotations = r.message || [];
                        if (!quotations.length) {
                            frappe.msgprint(__('No submitted quotations found for this customer.'));
                            return;
                        }

                        const dialog = new frappe.ui.Dialog({
                            title: __('Select Quotations'),
                            fields: [
                                {
                                    fieldname: 'quotation_table_wrapper',
                                    fieldtype: 'HTML',
                                }
                            ],
                            primary_action_label: __('Get Items'),
                            primary_action() {
                                const selected = Array.from(dialog.$wrapper.find('.quotation-checkbox:checked'))
                                    .map(el => el.dataset.quotation);

                                if (!selected.length) {
                                    frappe.msgprint(__('Please select at least one quotation.'));
                                    return;
                                }

                                frappe.call({
                                    method: 'fateh_logistics.api.get_items_from_multiple_quotations',
                                    args: {
                                        quotations: selected
                                    },
                                    callback: function (r) {
                                        if (r.message && r.message.items) {
                                            frm.clear_table('items');
                                            (r.message.items || []).forEach(q_item => {
                                                let item_row = frm.add_child("items");
                                                item_row.item = q_item.item_code;
                                                item_row.item_name = q_item.item_name;
                                                item_row.uom = q_item.uom;
                                                item_row.quantity = q_item.qty;
                                                item_row.rate = q_item.rate;
                                                item_row.amount = q_item.amount;
                                                item_row.from_quotation = q_item.parent;
                                            });
                                            frm.refresh_field('items');
                                            frm.events.update_totals(frm);
                                            dialog.hide();
                                        }
                                    }
                                });
                            }
                        });
                        dialog.show();

                        const table_html = `
                            <table class="table table-bordered">
                                <thead>
                                    <tr>
                                        <th><input type="checkbox" id="select-all-quotations" title="Select All" /></th>
                                        <th>Quotation</th>
                                        <th>Grand Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${quotations.map(q => `
                                        <tr>
                                            <td><input type="checkbox" class="quotation-checkbox" data-quotation="${q.name}"></td>
                                            <td>${q.name}</td>
                                            <td style="text-align:right;">${frappe.format(q.grand_total, { fieldtype: 'Currency' })}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        `;

                        dialog.fields_dict.quotation_table_wrapper.$wrapper.html(table_html);
                        dialog.$wrapper.find('#select-all-quotations').on('change', function () {
                            const checked = $(this).is(':checked');
                            dialog.$wrapper.find('.quotation-checkbox').prop('checked', checked);
                        });
                        dialog.$wrapper.on('change', '.quotation-checkbox', function () {
                            const total = dialog.$wrapper.find('.quotation-checkbox').length;
                            const checked = dialog.$wrapper.find('.quotation-checkbox:checked').length;
                            dialog.$wrapper.find('#select-all-quotations').prop('checked', total === checked);
                        });
                    }
                });
            });
        }
    },

    refresh: function (frm) {
        // Test: Show alert to verify refresh is called
        if (!frm.is_new() && window.location.search.indexOf('test=1') > -1) {
            frappe.show_alert({message: "Job Record refresh called", indicator: "blue"}, 3);
        }
        
        if (!frm.is_new()) {
            // Add custom buttons first (these should always show)
            frm.add_custom_button(__('View Trips'), function() {
                frappe.set_route("List", "Trip Details", { job_records: frm.doc.name });
            }, __("View"));


            // First check if "Expense Entry" doctype exists
            frappe.model.with_doctype("Expense Entry", function() {
                // Doctype exists, proceed with API call
                frappe.call({
                    method: "fateh_logistics.api.get_expense_entries_for_job",
                    args: {
                        job_record_id: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            let total_expenses = 0;
                            frm.clear_table("expenses");
                            r.message.forEach(function(row) {
                                let child = frm.add_child("expenses");
                                child.reference_doctype = row.reference_doctype;
                                child.reference_record = row.reference_record;
                                child.amount = row.amount;
                                total_expenses += row.amount;
                            });
                            frm.refresh_field("expenses");
                            frm.set_value("total_expense", total_expenses)

                            setTimeout(function() {
                                frm.doc.__unsaved = 0;
                                frm.page.clear_indicator();
                            }, 100);
                        }
                    }
                });
            }, function() {
                // Doctype does not exist
                frappe.msgprint(__('Expense Entry is not available on this site.'));
            });
            
            // Set dashboard indicators - run after client scripts have finished
            // Client scripts run after doctype JS, so we need to wait longer
            // Hook into form-render-complete event and also use multiple timeouts
            $(frm.wrapper).one('render_complete', function() {
                setTimeout(function() {
                    if (!frm.is_customizing() && frm.dashboard) {
                        frm.events.set_dashboard_indicators(frm);
                    }
                }, 2500);
            });
            
            // Also hook into dashboard after_refresh if available
            if (frm.dashboard) {
                var original_after_refresh = frm.dashboard.after_refresh;
                frm.dashboard.after_refresh = function() {
                    if (original_after_refresh) {
                        original_after_refresh.apply(this, arguments);
                    }
                    setTimeout(function() {
                        if (!frm.is_customizing() && frm.dashboard) {
                            frm.events.set_dashboard_indicators(frm);
                        }
                    }, 500);
                };
            }
            
            // Fallback: Try multiple times with increasing delays (after client scripts)
            [3000, 4000, 5000, 6000].forEach(function(delay) {
                setTimeout(function() {
                    if (!frm.is_customizing() && frm.dashboard) {
                        frm.events.set_dashboard_indicators(frm);
                    }
                }, delay);
            });
        }
    },

    set_dashboard_indicators: function (frm) {
        // Don't clear dashboard - let client scripts add their indicators too
        // Only add our indicators if dashboard exists
        if (!frm.dashboard) {
            return;
        }
        
        // Get currency - use default if not in doc
        var currency = frm.doc.currency || frappe.defaults.get_default("currency") || "SAR";
        
        function process_invoices(invoices, includeOutstanding = false) {
            var totals = { grandTotal: 0, outstandingTotal: 0 };
            if (invoices && invoices.length > 0) {
                invoices.forEach(function (invoice) {
                    totals.grandTotal += invoice.base_grand_total || 0;
                    if (includeOutstanding) {
                        totals.outstandingTotal += invoice.outstanding_amount || 0;
                    }
                });
            }
            return totals;
        }

        function process_journal_entries(entries) {
            var total = 0;
            if (entries && entries.length > 0) {
                entries.forEach(function (entry) {
                    total += entry.total || 0;
                });
            }
            return total;
        }

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Sales Invoice',
                filters: {
                    custom_job_record: frm.doc.name,
                    docstatus: 1
                },
                fields: ['base_grand_total', 'outstanding_amount']
            },
            callback: function (response) {
                var salesInvoiceTotals = process_invoices(response.message, true);

                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Purchase Invoice',
                        filters: {
                            custom_job_record: frm.doc.name,
                            docstatus: 1
                        },
                        fields: ['base_grand_total', 'outstanding_amount']
                    },
                    callback: function (response) {
                        var purchaseInvoiceTotals = process_invoices(response.message, true);

                        // Try Expense Entry first, fallback to Journal Entry if it doesn't exist
                        frappe.model.with_doctype("Expense Entry", function() {
                            // Expense Entry exists
                            frappe.call({
                                method: 'frappe.client.get_list',
                                args: {
                                    doctype: 'Expense Entry',
                                    filters: {
                                        custom_job_record: frm.doc.name,
                                        docstatus: 1,
                                        status: "Approved"
                                    },
                                    fields: ['total']
                                },
                                callback: function (response) {
                                    var journalEntryTotalDebit = process_journal_entries(response.message || []);
                                    frm.events.add_indicators_to_dashboard(frm, salesInvoiceTotals, purchaseInvoiceTotals, journalEntryTotalDebit, currency);
                                },
                                error: function(r) {
                                    // Fallback to Journal Entry
                                    frm.events.fetch_journal_entries(frm, salesInvoiceTotals, purchaseInvoiceTotals, currency);
                                }
                            });
                        }, function() {
                            // Expense Entry doesn't exist, use Journal Entry
                            frm.events.fetch_journal_entries(frm, salesInvoiceTotals, purchaseInvoiceTotals, currency);
                        });
                    },
                    error: function(r) {
                        // Error fetching Purchase Invoice
                    }
                });
            },
            error: function(r) {
                // Error fetching Sales Invoice
            }
        });
    },
    
    // Helper function to fetch Journal Entries
    fetch_journal_entries: function(frm, salesInvoiceTotals, purchaseInvoiceTotals, currency) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Journal Entry',
                filters: {
                    custom_job_record: frm.doc.name,
                    docstatus: 1
                },
                fields: ['total_debit']
            },
            callback: function (response) {
                var journalEntryTotalDebit = 0;
                if (response.message && response.message.length > 0) {
                    response.message.forEach(function(entry) {
                        journalEntryTotalDebit += entry.total_debit || 0;
                    });
                }
                frm.events.add_indicators_to_dashboard(frm, salesInvoiceTotals, purchaseInvoiceTotals, journalEntryTotalDebit, currency);
            },
            error: function(r) {
                // Still add indicators with 0 expenses
                frm.events.add_indicators_to_dashboard(frm, salesInvoiceTotals, purchaseInvoiceTotals, 0, currency);
            }
        });
    },
    
    // Helper function to add indicators to dashboard
    add_indicators_to_dashboard: function(frm, salesInvoiceTotals, purchaseInvoiceTotals, journalEntryTotalDebit, currency) {
        var totalExpenses = purchaseInvoiceTotals.grandTotal + journalEntryTotalDebit;
        var profitAndLoss = salesInvoiceTotals.grandTotal - totalExpenses;

        // Ensure dashboard still exists (might have been cleared)
        if (!frm.dashboard) {
            // Try to get dashboard again
            if (frm.$wrapper && frm.$wrapper.find('.form-dashboard').length) {
                // Dashboard element exists, try again after a moment
                setTimeout(function() {
                    if (frm.dashboard) {
                        frm.events.add_indicators_to_dashboard(frm, salesInvoiceTotals, purchaseInvoiceTotals, journalEntryTotalDebit, currency);
                    }
                }, 200);
            }
            return;
        }
        
        try {
            // Add indicators one by one to catch any errors
            if (salesInvoiceTotals.grandTotal > 0 || purchaseInvoiceTotals.grandTotal > 0 || journalEntryTotalDebit > 0) {
                frm.dashboard.add_indicator(
                    __('Total Sales: {0}', [format_currency(salesInvoiceTotals.grandTotal, currency)]),
                    'blue'
                );
                
                frm.dashboard.add_indicator(
                    __('Total Purchase: {0}', [format_currency(purchaseInvoiceTotals.grandTotal, currency)]),
                    'orange'
                );
                
                frm.dashboard.add_indicator(
                    __('Other Expenses: {0}', [format_currency(journalEntryTotalDebit, currency)]),
                    'purple'
                );

                let stat = profitAndLoss >= 0 ? 'Profit' : 'Loss'
                frm.dashboard.add_indicator(
                    __('{0}: {1}', [stat, format_currency(profitAndLoss, currency)]),
                    profitAndLoss >= 0 ? 'green' : 'red'
                );
            }
        } catch (e) {
            // Error adding dashboard indicators
        }
    },

    update_totals: function (frm) {
        let total_qty = 0;
        let total_amt = 0;

        frm.doc.items.forEach(row => {
            total_qty += flt(row.quantity);
            total_amt += flt(row.amount);
        });

        frm.set_value('total_quantity', total_qty);
        frm.set_value('total_amount', total_amt);
    },

    load_quotation: function(frm) {
        if (frm.is_new() && frm.doc.quotation) {
            frappe.db.get_doc("Quotation", frm.doc.quotation)
                .then(quotation => {
                    if (quotation.quotation_to === "Customer") {
                        frm.set_value("customer", quotation.party_name);
                    }
                    frm.clear_table("items");
                    (quotation.items || []).forEach(q_item => {
                        let item_row = frm.add_child("items");
                        item_row.item = q_item.item_code;
                        item_row.item_name = q_item.item_name;
                        item_row.uom = q_item.uom;
                        item_row.quantity = q_item.qty;
                        item_row.rate = q_item.rate;
                        item_row.amount = q_item.amount;
                        item_row.from_quotation = q_item.parent;
                    });
                    frm.refresh_field("items");
                    frm.events.update_totals(frm);
                });
        }
    }
});


frappe.ui.form.on('Job Item Detail', {
    item: async function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.item) return;
        frappe.model.set_value(cdt, cdn, 'quantity', 1);

        try {
            let r = await frappe.db.get_value('Item Price', {
                item_code: row.item,
                price_list: 'Standard Selling'
            }, 'price_list_rate');

            if (r && r.message) {
                frappe.model.set_value(cdt, cdn, 'rate', r.message.price_list_rate);
                frappe.model.set_value(cdt, cdn, 'amount', r.message.price_list_rate * row.quantity);
            } else {
                frappe.model.set_value(cdt, cdn, 'rate', 0);
                frappe.msgprint(__('No Standard Selling price found for item {0}', [row.item]));
            }
        } catch (err) {
            // Error fetching price
            frappe.msgprint(__('Error fetching price for item {0}', [row.item]));
        }

        frm.events.update_totals(frm);
    },

    quantity: function (frm, cdt, cdn) {
        row = locals[cdt][cdn];

        if (row.quantity && row.rate) {
            frappe.model.set_value(cdt, cdn, "amount", row.quantity * row.rate)
        }

        frm.events.update_totals(frm);
        
    },

    rate: function (frm, cdt, cdn) {
        row = locals[cdt][cdn];

        if (row.quantity && row.rate) {
            frappe.model.set_value(cdt, cdn, "amount", row.quantity * row.rate)
        }

        frm.events.update_totals(frm);
        
    },

    items_remove: function (frm) {
        frm.events.update_totals(frm);
    }
});

frappe.ui.form.on('Job Assignment', {
    driver_type: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        
        // Clear driver if it doesn't match the selected driver_type
        if (row.driver && row.driver_type) {
            frappe.db.get_value('Driver', row.driver, 'employee').then(driver_res => {
                const has_employee = driver_res.message.employee;
                if ((row.driver_type === 'Own' && !has_employee) || 
                    (row.driver_type === 'External' && has_employee)) {
                    frappe.model.set_value(cdt, cdn, 'driver', '');
                    frappe.model.set_value(cdt, cdn, 'vehicle', '');
                }
            });
        }
        
        // Clear vehicle if it doesn't match the selected driver_type
        if (row.vehicle && row.driver_type) {
            frappe.db.get_value('Vehicle', row.vehicle, 'custom_is_external').then(vehicle_res => {
                const vehicle_type = vehicle_res.message.custom_is_external;
                if ((row.driver_type === 'Own' && vehicle_type !== 'Internal') || 
                    (row.driver_type === 'External' && vehicle_type !== 'External')) {
                    frappe.model.set_value(cdt, cdn, 'vehicle', '');
                }
            });
        }
        
        // Clear driver field when driver_type changes so user can select from filtered list
        frappe.model.set_value(cdt, cdn, 'driver', '');
        // Don't clear vehicle here - let the check above handle it based on vehicle type
    },
    
    driver: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (row.driver) {
            frappe.db.get_value('Driver', row.driver, ['employee', 'transporter']).then(driver_res => {
                const employee_id = driver_res.message.employee;
                
                // Auto-set driver_type based on employee if not already set
                if (employee_id && !row.driver_type) {
                    frappe.model.set_value(cdt, cdn, 'driver_type', 'Own');
                } else if (!employee_id && !row.driver_type) {
                    frappe.model.set_value(cdt, cdn, 'driver_type', 'External');
                }
                
                // If driver_type is Own, get vehicle for employee
                if (employee_id && row.driver_type === 'Own') {
                    frappe.db.get_list('Vehicle', {
                        filters: { employee: employee_id },
                        fields: ['name'],
                        limit: 1
                    }).then(vehicle_res => {
                        if (vehicle_res.length) {
                            frappe.model.set_value(cdt, cdn, 'vehicle', vehicle_res[0].name);
                        } else {
                            frappe.model.set_value(cdt, cdn, 'vehicle', '');
                        }
                    });
                } else if (row.driver_type === 'External') {
                    frappe.model.set_value(cdt, cdn, 'vehicle', '');
                }
            });
        } else {
            frappe.model.set_value(cdt, cdn, 'vehicle', '');
        }
    }
});

