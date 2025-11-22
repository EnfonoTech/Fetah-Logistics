// Copyright (c) 2025, siva@enfono.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Job Record", {
    onload: function (frm) {
        frm.events.load_quotation(frm);
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
        frm.events.set_dashboard_indicators(frm);

        if (!frm.is_new()) {
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
        }
    },

    set_dashboard_indicators: function (frm) {
        function process_invoices(invoices, includeOutstanding = false) {
            var totals = { grandTotal: 0, outstandingTotal: 0 };
            if (invoices && invoices.length > 0) {
                invoices.forEach(function (invoice) {
                    totals.grandTotal += invoice.base_grand_total;
                    if (includeOutstanding) {
                        totals.outstandingTotal += invoice.outstanding_amount;
                    }
                });
            }
            return totals;
        }

        function process_journal_entries(entries) {
            var total = 0;
            if (entries && entries.length > 0) {
                entries.forEach(function (entry) {
                    total += entry.total;
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
                                var journalEntryTotalDebit = process_journal_entries(response.message);

                                var totalExpenses = purchaseInvoiceTotals.grandTotal + journalEntryTotalDebit;
                                var profitAndLoss = salesInvoiceTotals.grandTotal - totalExpenses;

                                frm.dashboard.add_indicator(
                                    __('Total Sales: {0}', [format_currency(salesInvoiceTotals.grandTotal, frm.doc.currency)]),
                                    'blue'
                                );
                                frm.dashboard.add_indicator(
                                    __('Total Purchase: {0}', [format_currency(purchaseInvoiceTotals.grandTotal, frm.doc.currency)]),
                                    'orange'
                                );
                                frm.dashboard.add_indicator(
                                    __('Other Expenses: {0}', [format_currency(journalEntryTotalDebit, frm.doc.currency)]),
                                    'purple'
                                );

                                let stat = profitAndLoss >= 0 ? 'Profit' : 'Loss'
                                frm.dashboard.add_indicator(
                                    __('{0}: {1}', [stat, format_currency(profitAndLoss, frm.doc.currency)]),
                                    profitAndLoss >= 0 ? 'green' : 'red'
                                );
                            }
                        });
                    }
                });
            }
        });
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
            console.error('Error fetching price:', err);
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

