// Copyright (c) 2025, siva and contributors
// For license information, please see license.txt
frappe.ui.form.on("Trip Details", {
	refresh(frm) {

	},
});




// frappe.ui.form.on("Trip Details", {
// 	refresh(frm) {
// 		// Show "Create Purchase Invoice" button if document is saved and has driver
// 		// Server will validate if driver is external and has allowance
// 		if (!frm.is_new() && frm.doc.driver) {
// 			frm.add_custom_button(__('Create Purchase Invoice'), function() {
// 				if (!frm.doc.allowance) {
// 					frappe.msgprint({
// 						title: __('Validation Error'),
// 						indicator: 'orange',
// 						message: __('Please set allowance in Trip Details before creating Purchase Invoice.')
// 					});
// 					return;
// 				}
				
// 				frappe.call({
// 					method: 'fateh_logistics.fateh_logistics.doctype.trip_details.trip_details.make_purchase_invoice',
// 					args: {
// 						source_name: frm.doc.name
// 					},
// 					freeze: true,
// 					freeze_message: __('Creating Purchase Invoice...'),
// 					callback: function(r) {
// 						if (r.message && !r.exc) {
// 							// Sync the document to client
// 							frappe.model.sync(r.message);
// 							// Open the document
// 							frappe.set_route("Form", r.message.doctype, r.message.name);
// 						} else if (r.exc) {
// 							frappe.msgprint({
// 								title: __('Error'),
// 								indicator: 'red',
// 								message: __('Error creating Purchase Invoice: {0}', [r.exc])
// 							});
// 						}
// 					}
// 				});
// 			}, __('Create'));
// 		}
		
// 		// Update Purchase Invoice status field
// 		if (!frm.is_new()) {
// 			frm.events.update_purchase_invoice_status(frm);
// 		}
// 	},
	
// 	update_purchase_invoice_status: function(frm) {
// 		// Check if driver is external
// 		if (frm.doc.driver) {
// 			frappe.db.get_value('Driver', frm.doc.driver, ['employee', 'transporter']).then(function(r) {
// 				if (r.message) {
// 					const is_external = !r.message.employee && r.message.transporter;
					
// 					// Get Purchase Invoice linked to this Trip Details
// 					frappe.db.get_list('Purchase Invoice', {
// 						filters: {
// 							custom_trip_details: frm.doc.name
// 						},
// 						fields: ['name', 'docstatus', 'status'],
// 						limit: 1
// 					}).then(function(pi_list) {
// 						let status_text = '';
// 						let pi_name = '';
						
// 						if (pi_list && pi_list.length > 0) {
// 							const pi = pi_list[0];
// 							pi_name = pi.name;
							
// 							if (pi.docstatus === 1) {
// 								status_text = 'Submitted';
// 							} else if (pi.docstatus === 0) {
// 								status_text = 'Draft';
// 							} else if (pi.docstatus === 2) {
// 								status_text = 'Cancelled';
// 							}
// 						} else {
// 							if (is_external) {
// 								status_text = 'Not Created';
// 							}
// 						}
						
// 						// Update the status field
// 						frm.set_value('custom_purchase_invoice_status', status_text);
						
// 						// Update the Purchase Invoice link field
// 						if (pi_name) {
// 							frm.set_value('custom_purchase_invoice', pi_name);
// 						} else {
// 							frm.set_value('custom_purchase_invoice', '');
// 						}
// 					});
// 				}
// 			});
// 		} else {
// 			// No driver selected
// 			frm.set_value('custom_purchase_invoice_status', '');
// 			frm.set_value('custom_purchase_invoice', '');
// 		}
// 	}
// });