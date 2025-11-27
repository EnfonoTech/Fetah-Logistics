// Copyright (c) 2025, siva@enfono.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Vehicle", {
    refresh: function (frm) {
        if (!frm.is_new()) {
            frm.events.set_financial_indicators(frm);
        }
    },

    set_financial_indicators: function (frm) {
        try {
            // Check if license_plate exists
            if (!frm.doc.license_plate) {
                console.warn('Vehicle license_plate not found, skipping dashboard');
                return;
            }

            function process_invoices(invoices, includeOutstanding = false) {
                var totals = {
                    grandTotal: 0,
                    baseTotal: 0,
                    outstandingTotal: 0
                };
                if (invoices && invoices.length > 0) {
                    invoices.forEach(function (invoice) {
                        totals.grandTotal += invoice.base_grand_total || 0;
                        totals.baseTotal += invoice.base_total || 0;
                        if (includeOutstanding) {
                            totals.outstandingTotal += invoice.outstanding_amount || 0;
                        }
                    });
                }
                return totals;
            }

            function process_journal_entries(entries) {
                var totalDebit = 0;
                if (entries && entries.length > 0) {
                    entries.forEach(function (entry) {
                        totalDebit += entry.total_debit || 0;
                    });
                }
                return totalDebit;
            }

            // Query Sales Invoices using custom API method (queries child table)
        frappe.call({
            method: 'fateh_logistics.api.get_sales_invoices_for_vehicle',
            args: {
                vehicle: frm.doc.license_plate
            },
            callback: function (response) {
                if (!response || !response.message) {
                    console.error('Sales Invoice query failed:', response);
                    // Try to continue with Purchase Invoice only
                    frappe.call({
                        method: 'fateh_logistics.api.get_purchase_invoices_for_vehicle',
                        args: {
                            vehicle: frm.doc.license_plate
                        },
                        callback: function (piResponse) {
                            if (piResponse && piResponse.message) {
                                var purchaseInvoiceTotals = process_invoices(piResponse.message, true);
                                var currency = piResponse.message && piResponse.message.length > 0 ? piResponse.message[0].currency : 'SAR';
                                show_indicators(frm, {baseTotal: 0}, purchaseInvoiceTotals, 0, -purchaseInvoiceTotals.baseTotal, currency);
                            } else {
                                show_indicators(frm, {baseTotal: 0}, {baseTotal: 0}, 0, 0, 'SAR');
                            }
                        },
                        error: function (r) {
                            console.error('Purchase Invoice query error:', r);
                            show_indicators(frm, {baseTotal: 0}, {baseTotal: 0}, 0, 0, 'SAR');
                        }
                    });
                    return;
                }
                var salesInvoiceTotals = process_invoices(response.message, true);
                var currency = response.message && response.message.length > 0 ? response.message[0].currency : 'SAR';

                // Query Purchase Invoices using custom API method (queries child table)
                frappe.call({
                    method: 'fateh_logistics.api.get_purchase_invoices_for_vehicle',
                    args: {
                        vehicle: frm.doc.license_plate
                    },
                    callback: function (piResponse) {
                        if (!piResponse || !piResponse.message) {
                            console.error('Purchase Invoice query failed:', piResponse);
                            // Show dashboard with just Sales Invoice if Purchase fails
                            show_indicators(frm, salesInvoiceTotals, {baseTotal: 0}, 0, salesInvoiceTotals.baseTotal, currency);
                            return;
                        }
                        var purchaseInvoiceTotals = process_invoices(piResponse.message, true);
                        if (piResponse.message && piResponse.message.length > 0 && !currency) {
                            currency = piResponse.message[0].currency;
                        }

                        // Query Journal Entries using custom API method
                        frappe.call({
                            method: 'fateh_logistics.api.get_journal_entries_for_vehicle',
                            args: {
                                vehicle: frm.doc.license_plate
                            },
                            callback: function (jeResponse) {
                                var journalEntryTotalDebit = 0;
                                if (jeResponse && jeResponse.message && jeResponse.message.length > 0) {
                                    journalEntryTotalDebit = process_journal_entries(jeResponse.message);
                                    if (!currency && jeResponse.message[0].total_amount_currency) {
                                        currency = jeResponse.message[0].total_amount_currency;
                                    }
                                }

                                var totalExpenses = purchaseInvoiceTotals.baseTotal + journalEntryTotalDebit;
                                var profitAndLoss = salesInvoiceTotals.baseTotal - totalExpenses;

                                show_indicators(frm, salesInvoiceTotals, purchaseInvoiceTotals, journalEntryTotalDebit, profitAndLoss, currency);
                            },
                            error: function (r) {
                                console.error('Journal Entry query error:', r);
                                // If query fails, show without Journal Entries
                                var totalExpenses = purchaseInvoiceTotals.baseTotal;
                                var profitAndLoss = salesInvoiceTotals.baseTotal - totalExpenses;
                                show_indicators(frm, salesInvoiceTotals, purchaseInvoiceTotals, 0, profitAndLoss, currency);
                            }
                        });
                    },
                    error: function (r) {
                        console.error('Purchase Invoice query error:', r);
                        // Show dashboard with just Sales Invoice if Purchase fails
                        show_indicators(frm, salesInvoiceTotals, {baseTotal: 0}, 0, salesInvoiceTotals.baseTotal, currency);
                    }
                });
            },
            error: function (r) {
                console.error('Sales Invoice query error:', r);
                // If Sales Invoice query fails, try to show at least Purchase Invoice
                frappe.call({
                    method: 'fateh_logistics.api.get_purchase_invoices_for_vehicle',
                    args: {
                        vehicle: frm.doc.license_plate
                    },
                    callback: function (piResponse) {
                        if (piResponse && piResponse.message) {
                            var purchaseInvoiceTotals = process_invoices(piResponse.message, true);
                            var currency = piResponse.message && piResponse.message.length > 0 ? piResponse.message[0].currency : 'SAR';
                            show_indicators(frm, {baseTotal: 0}, purchaseInvoiceTotals, 0, -purchaseInvoiceTotals.baseTotal, currency);
                        } else {
                            show_indicators(frm, {baseTotal: 0}, {baseTotal: 0}, 0, 0, 'SAR');
                        }
                    },
                    error: function (r2) {
                        console.error('Purchase Invoice query error:', r2);
                        show_indicators(frm, {baseTotal: 0}, {baseTotal: 0}, 0, 0, 'SAR');
                    }
                });
            }
        });
        } catch (error) {
            console.error('Error setting financial indicators:', error);
            // Show empty dashboard on error
            try {
                show_indicators(frm, {baseTotal: 0}, {baseTotal: 0}, 0, 0, 'SAR');
            } catch (e) {
                console.error('Error showing indicators:', e);
            }
        }
    }
});

function show_indicators(frm, salesInvoiceTotals, purchaseInvoiceTotals, journalEntryTotalDebit, profitAndLoss, currency) {
    frm.dashboard.add_indicator(
        __('Sales Invoice (W/O VAT): {0}', [format_currency(salesInvoiceTotals.baseTotal, currency || 'SAR')]),
        'blue'
    );

    frm.dashboard.add_indicator(
        __('Purchase Invoice (W/O VAT): {0}', [format_currency(purchaseInvoiceTotals.baseTotal, currency || 'SAR')]),
        'orange'
    );
    
    if (journalEntryTotalDebit > 0) {
        frm.dashboard.add_indicator(
            __('Journal Entries: {0}', [format_currency(journalEntryTotalDebit, currency || 'SAR')]),
            'purple'
        );
    }
    
    frm.dashboard.add_indicator(
        __('P&L: {0}', [format_currency(profitAndLoss, currency || 'SAR')]),
        profitAndLoss >= 0 ? 'green' : 'red'
    );
}
