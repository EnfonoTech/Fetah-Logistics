frappe.ui.form.on("Job Record", {

    onload(frm) {

        frm.events.load_quotation(frm);

        frm.set_query('driver', 'job_assignment', (doc, cdt, cdn) => {
            const row = locals[cdt][cdn];
            if (row.driver_type === 'Own') {
                return {
                    query: 'fateh_logistics.api.get_drivers_by_type',
                    filters: { driver_type: 'Own' }
                };
            }
            if (row.driver_type === 'External') {
                return {
                    query: 'fateh_logistics.api.get_drivers_by_type',
                    filters: { driver_type: 'External' }
                };
            }
            return {};
        });

        frm.set_query('vehicle', 'job_assignment', (doc, cdt, cdn) => {
            const row = locals[cdt][cdn];
            if (row.driver_type === 'Own') return { filters: { custom_is_external: 'Internal' } };
            if (row.driver_type === 'External') return { filters: { custom_is_external: 'External' } };
            return {};
        });
    },

    customer(frm) {

        frm.clear_custom_buttons();

        if (!frm.is_new() || !frm.doc.customer) return;

        frm.add_custom_button(__('Get Items from Quotation'), () => {

            frappe.call({
                method: 'fateh_logistics.api.get_quotations_for_customer',
                args: { customer: frm.doc.customer },

                callback(r) {

                    const quotations = r.message || [];

                    if (!quotations.length) {
                        frappe.msgprint(__('No submitted quotations found for this customer.'));
                        return;
                    }

                    const dialog = new frappe.ui.Dialog({
                        title: __('Select Quotations'),
                        fields: [{ fieldname: 'quotation_table_wrapper', fieldtype: 'HTML' }],
                        primary_action_label: __('Get Items'),

                        primary_action() {

                            const selected = dialog.$wrapper
                                .find('.quotation-checkbox:checked')
                                .map((i, el) => el.dataset.quotation)
                                .get();

                            if (!selected.length) {
                                frappe.msgprint(__('Please select at least one quotation.'));
                                return;
                            }

                            frappe.call({
                                method: 'fateh_logistics.api.get_items_from_multiple_quotations',
                                args: { quotations: selected },

                                callback(res) {

                                    if (!res.message || !res.message.items) return;

                                    frm.clear_table('items');

                                    res.message.items.forEach(item => {
                                        let row = frm.add_child("items");
                                        row.item = item.item_code;
                                        row.item_name = item.item_name;
                                        row.uom = item.uom;
                                        row.quantity = item.qty;
                                        row.rate = item.rate;
                                        row.amount = item.amount;
                                        row.from_quotation = item.parent;
                                    });

                                    frm.refresh_field('items');
                                    frm.events.update_totals(frm);
                                    dialog.hide();
                                }
                            });
                        }
                    });

                    dialog.show();

                    const table_html = `
                        <table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th><input type="checkbox" id="select-all-quotations"></th>
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
                        dialog.$wrapper.find('.quotation-checkbox').prop('checked', this.checked);
                    });
                }
            });
        });
    },

    refresh(frm) {

        if (frm.is_new()) return;

        frm.add_custom_button(__('View Trips'), () => {
            frappe.set_route("List", "Trip Details", { job_records: frm.doc.name });
        }, __("View"));

        frm.add_custom_button(__('Create Trip Details'), function () {

            let pending_rows = (frm.doc.job_assignment || [])
                .filter(r => r.trip_detail_status === "Pending");

            if (!pending_rows.length) {
                frappe.msgprint("No Pending Trips Found.");
                return;
            }

            const required_fields = {
                driver: "Driver",
                vehicle: "Vehicle"
            };

            let errors = [];

            pending_rows.forEach(row => {
                let rn = row.idx || "?";
                Object.keys(required_fields).forEach(field => {
                    if (!row[field]) {
                        errors.push(`Row ${rn}: Missing ${required_fields[field]}`);
                    }
                });
            });

            if (errors.length) {
                frappe.msgprint({ title: "Validation Errors", indicator: "red", message: errors.join("<br>") });
                return;
            }

            function create_trip(index) {

                if (index >= pending_rows.length) {

                    frm.save().then(() => {
                        frappe.msgprint("All Trips Created Successfully");
                        frm.reload_doc();
                    });

                    return;
                }

                let row = pending_rows[index];

                frappe.call({
                    method: 'fateh_logistics.api.create_trip_details',
                    args: {
                        job_record: frm.doc.name,
                        job_assignment: row.name,   
                        driver: row.driver,
                        vehicle: row.vehicle,
                        trip_amount: row.trip_amount,
                        allowance: row.allowance || 0,
                        vehicle_revenue: row.vehicle_revenue || 0
                    },
                    callback(r) {

                        if (!r.message) {
                            frappe.msgprint("Trip created but server did not return any ID.");
                            return;
                        }
                    
                        row.__creating_trip = true;
                    
                        frappe.model.set_value(row.doctype, row.name, "trip_detail_status", "Created");
                    
                        frappe.show_alert({
                            message: __('Trip Created: ' + r.message.trip_name),
                            indicator: 'green'
                        }, 5);
                    
                        setTimeout(() => { delete row.__creating_trip; }, 500);
                    
                        if (index === pending_rows.length - 1) {
                            frm.save().then(() => {
                                frappe.set_route("Form", "Trip Details", r.message.trip_name);

                            });
                        }
                    
                        create_trip(index + 1);
                    }
                    
                });
                
            }

            create_trip(0);
        });

        frappe.model.with_doctype("Expense Entry", () => {

            frappe.call({
                method: "fateh_logistics.api.get_expense_entries_for_job",
                args: { job_record_id: frm.doc.name },

                callback(r) {

                    if (!r.message) return;

                    let total = 0;
                    frm.clear_table("expenses");

                    r.message.forEach(row => {
                        let child = frm.add_child("expenses");
                        child.reference_doctype = row.reference_doctype;
                        child.reference_record = row.reference_record;
                        child.amount = row.amount;
                        total += row.amount;
                    });

                    frm.refresh_field("expenses");
                    frm.set_value("total_expense", total);

                    setTimeout(() => {
                        frm.doc.__unsaved = 0;
                        frm.page.clear_indicator();
                    }, 100);
                }
            });
        });

        setTimeout(() => {
            if (frm.dashboard) frm.events.set_dashboard_indicators(frm);
        }, 2000);
    },

    set_dashboard_indicators(frm) {

        if (!frm.dashboard) return;

        const currency = frm.doc.currency || frappe.defaults.get_default("currency") || "SAR";

        function sum(rows, key) {
            return (rows || []).reduce((a, r) => a + (r[key] || 0), 0);
        }

        frappe.client.get_list('Sales Invoice', {
            filters: { custom_job_record: frm.doc.name, docstatus: 1 },
            fields: ['base_grand_total']
        }).then(salesRes => {

            const sales = sum(salesRes, 'base_grand_total');

            frappe.client.get_list('Purchase Invoice', {
                filters: { custom_job_record: frm.doc.name, docstatus: 1 },
                fields: ['base_grand_total']
            }).then(purchaseRes => {

                const purchase = sum(purchaseRes, 'base_grand_total');

                frappe.client.get_list('Expense Entry', {
                    filters: { custom_job_record: frm.doc.name, docstatus: 1, status: 'Approved' },
                    fields: ['total']
                }).then(expRes => {

                    const other = sum(expRes, 'total');
                    const profit = sales - (purchase + other);

                    frm.dashboard.add_indicator(`Sales: ${format_currency(sales, currency)}`, "blue");
                    frm.dashboard.add_indicator(`Purchase: ${format_currency(purchase, currency)}`, "orange");
                    frm.dashboard.add_indicator(`Other Expenses: ${format_currency(other, currency)}`, "purple");
                    frm.dashboard.add_indicator(
                        `${profit >= 0 ? 'Profit' : 'Loss'}: ${format_currency(profit, currency)}`,
                        profit >= 0 ? "green" : "red"
                    );
                });
            });
        });
    },

    update_totals(frm) {

        let total_qty = 0;
        let total_amt = 0;

        (frm.doc.items || []).forEach(row => {
            total_qty += flt(row.quantity);
            total_amt += flt(row.amount);
        });

        frm.set_value('total_quantity', total_qty);
        frm.set_value('total_amount', total_amt);
    },

    load_quotation(frm) {

        if (!frm.is_new() || !frm.doc.quotation) return;

        frappe.db.get_doc("Quotation", frm.doc.quotation).then(q => {

            frm.set_value("customer", q.party_name);
            frm.clear_table("items");

            (q.items || []).forEach(i => {
                let row = frm.add_child("items");
                row.item = i.item_code;
                row.item_name = i.item_name;
                row.uom = i.uom;
                row.quantity = i.qty;
                row.rate = i.rate;
                row.amount = i.amount;
                row.from_quotation = i.parent;
            });

            frm.refresh_field("items");
            frm.events.update_totals(frm);
        });
    }

});


frappe.ui.form.on('Job Item Detail', {

    async item(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.item) return;

        frappe.model.set_value(cdt, cdn, 'quantity', 1);

        const r = await frappe.db.get_value(
            'Item Price',
            { item_code: row.item, price_list: 'Standard Selling' },
            'price_list_rate'
        );

        let rate = r.message ? r.message.price_list_rate : 0;

        frappe.model.set_value(cdt, cdn, 'rate', rate);
        frappe.model.set_value(cdt, cdn, 'amount', rate);
        frm.events.update_totals(frm);
    },

    quantity(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", row.quantity * row.rate);
        frm.events.update_totals(frm);
    },

    rate(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", row.quantity * row.rate);
        frm.events.update_totals(frm);
    },

    items_remove(frm) {
        frm.events.update_totals(frm);
    }
});


frappe.ui.form.on('Job Assignment', {

    trip_amount(frm, cdt, cdn) {

        let row = locals[cdt][cdn];
        let amount = flt(row.trip_amount) || 0;
    
        let allowance = 0;
    
        if (row.driver_type === "Own") {
    
            let allowance_rate = flt(frm.doc.allowance_amount) || 0;
            allowance = amount * allowance_rate;
    
            frappe.model.set_value(cdt, cdn, 'allowance', allowance);
    
        } else if (row.driver_type === "External") {
    
            allowance = amount;
    
            frappe.model.set_value(cdt, cdn, 'allowance', allowance);
            frappe.model.set_value(cdt, cdn, 'vehicle_revenue', allowance); 
        }
    
        if (!row.__creating_trip) {
            frappe.model.set_value(cdt, cdn, 'trip_detail_status', 'Pending');
        }
    },
    
    

    driver_type(frm, cdt, cdn) {

        let row = locals[cdt][cdn];

        if (!row.__creating_trip) {
            frappe.model.set_value(cdt, cdn, 'trip_detail_status', 'Pending');
        }

        // Reset always
        frappe.model.set_value(cdt, cdn, 'driver', '');
        frappe.model.set_value(cdt, cdn, 'vehicle', '');

    },

    driver(frm, cdt, cdn) {

        const row = locals[cdt][cdn];

        if (!row.__creating_trip) {
            frappe.model.set_value(cdt, cdn, 'trip_detail_status', 'Pending');
        }

        if (!row.driver) {
            frappe.model.set_value(cdt, cdn, 'vehicle', '');
            frappe.model.set_value(cdt, cdn, 'transporter', '');
            return;
        }

        frappe.db.get_value('Driver', row.driver, ['employee', 'transporter']).then(r => {

            const employee = r.message.employee;
            const transporter = r.message.transporter;

            // AUTO DETECT DRIVER TYPE
            if (employee) {
                frappe.model.set_value(cdt, cdn, 'driver_type', 'Own');
            } else {
                frappe.model.set_value(cdt, cdn, 'driver_type', 'External');
            }

            // SET TRANSPORTER IF EXTERNAL DRIVER
            if (!employee && transporter) {
                frappe.model.set_value(cdt, cdn, 'transporter', transporter);
            } else {
                frappe.model.set_value(cdt, cdn, 'transporter', '');
            }

          
            if (employee) {
                frappe.db.get_list('Vehicle', {
                    filters: { employee: employee },
                    fields: ['name'],
                    limit: 1
                }).then(v => {
                    frappe.model.set_value(cdt, cdn, 'vehicle', v.length ? v[0].name : '');
                });
            }

            if (!employee && transporter) {
                frappe.db.get_list('Vehicle', {
                    filters: { custom_transporter: transporter },
                    fields: ['name'],
                    limit: 1
                }).then(v => {

                    frappe.model.set_value(cdt, cdn, 'vehicle', v.length ? v[0].name : '');

                    if (!v.length) {
                        frappe.msgprint(__('No vehicle linked to this transporter'));
                    }

                });
            }

        });

    },

    vehicle(frm, cdt, cdn) {

        let row = locals[cdt][cdn];

        if (!row.__creating_trip) {
            frappe.model.set_value(cdt, cdn, 'trip_detail_status', 'Pending');
        }

        if (row.vehicle && row.driver_type) {
            frappe.db.get_value('Vehicle', row.vehicle, 'custom_is_external').then(r => {
                const type = r.message.custom_is_external;

                if (
                    (row.driver_type === 'Own' && type !== 'Internal') ||
                    (row.driver_type === 'External' && type !== 'External')
                ) {
                    frappe.msgprint("Vehicle does not match Driver Type");
                    frappe.model.set_value(cdt, cdn, 'vehicle', '');
                }
            });
        }
    }

});


frappe.ui.form.on("Job Record", {

    refresh(frm) {

        if (frm.doc.__islocal) return;

        if (frm.doc.invoice_status !== "Invoice Created") {
            frm.add_custom_button("Create Sales Invoice", () => {
                frm.events.create_sales_invoice(frm);
            });
        }

        // ------------------------------------------------
        // FILTER ITEM TAX TEMPLATE BY COMPANY (CHILD TABLE)
        // ------------------------------------------------
        frm.set_query("item_tax_template", "invoice_item", function (doc, cdt, cdn) {
            if (!frm.doc.company) return {};
            return {
                filters: {
                    company: frm.doc.company
                }
            };
        });
    },

    async create_sales_invoice(frm) {

        // ---------------------------
        // CHECK DUPLICATE
        // ---------------------------
        const existing_invoice = await frappe.db.get_list("Sales Invoice", {
            filters: { custom_job_record: frm.doc.name },
            fields: ["name", "docstatus"],
            limit: 1
        });

        if (existing_invoice.length && existing_invoice[0].docstatus !== 2) {
            frappe.msgprint({
                title: __("Duplicate Invoice"),
                message: __("A Sales Invoice already exists for this Job Record."),
                indicator: "red"
            });
            return;
        }

        // ---------------------------
        // BASIC VALIDATION
        // ---------------------------
        if (!frm.doc.invoice_item || !frm.doc.invoice_item.length) {
            frappe.msgprint({
                title: __("No Items"),
                message: __("Please add at least one row in Invoice Items."),
                indicator: "red"
            });
            return;
        }

        if (!frm.doc.company || !frm.doc.customer) {
            frappe.msgprint({
                title: __("Missing Data"),
                message: __("Company and Customer are required."),
                indicator: "red"
            });
            return;
        }

        // ---------------------------
        // BUILD ITEMS + ITEM-WISE TAX
        // ---------------------------
        let items = [];
        let tax_accounts = {};   // tax heads for header

        for (let row of frm.doc.invoice_item) {

            if (!row.item || !row.qty || !row.rate) {
                frappe.throw(__("Item, Qty and Rate are mandatory in Invoice Items"));
            }

            let item_tax_rate = null;

            if (row.item_tax_template) {

                const tax_doc = await frappe.db.get_doc(
                    "Item Tax Template",
                    row.item_tax_template
                );

                if (tax_doc.taxes && tax_doc.taxes.length) {

                    let tax_map = {};

                    tax_doc.taxes.forEach(t => {
                        tax_map[t.tax_type] = t.tax_rate;
                        tax_accounts[t.tax_type] = true; // collect header tax head
                    });

                    item_tax_rate = JSON.stringify(tax_map);
                }
            }

            items.push({
                item_code: row.item,
                qty: row.qty,
                rate: row.rate,
                item_tax_template: row.item_tax_template || null,
                item_tax_rate: item_tax_rate,   // ✅ item-wise VAT
                custom_container_no: frm.doc.custom_container_no
            });
        }

        // ---------------------------
        // HEADER TAX ROWS (RATE = 0)
        // ---------------------------
        let taxes = Object.keys(tax_accounts).map(acc => ({
            charge_type: "On Net Total",
            account_head: acc,
            description: acc,
            rate: 0,                     // item-wise tax will apply
            included_in_print_rate: 0
        }));

        // ---------------------------
        // CREATE SALES INVOICE
        // ---------------------------
        frappe.call({
            method: "frappe.client.insert",
            args: {
                doc: {
                    doctype: "Sales Invoice",
                    company: frm.doc.company,
                    customer: frm.doc.customer,
                    cost_center: frm.doc.branch,
                    posting_date: frappe.datetime.get_today(),
                    custom_job_record: frm.doc.name,
                    items: items,
                    taxes: taxes
                }
            },
            callback(r) {
                if (!r.exc) {

                    frappe.db.set_value(
                        "Job Record",
                        frm.doc.name,
                        "invoice_status",
                        "Invoice Created"
                    );

                    frappe.msgprint({
                        message: __("Sales Invoice created successfully (Draft)"),
                        indicator: "green"
                    });

                    frappe.set_route("Form", "Sales Invoice", r.message.name);
                }
            }
        });
    }
});
