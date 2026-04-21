// Copyright (c) 2026, ramees@enfono.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rent Details", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.total_rent > 0 && !frm.doc.sales_invoice) {
			frm.add_custom_button(__('Sales Invoice'), function () {
				frappe.call({
					method: 'fateh_logistics.fateh_logistics.doctype.rent_details.rent_details.make_sales_invoice',
					args: { source_name: frm.doc.name },
					freeze: true,
					freeze_message: __('Creating Sales Invoice...'),
					callback: function (r) {
						if (r.message) {
							frm.reload_doc();
							frappe.set_route("Form", "Sales Invoice", r.message);
						}
					}
				});
			}, __('Create'));
		}
	},

	project(frm) {
		if (frm.doc.project) {
			frappe.db.get_value('Project', frm.doc.project, 'customer').then(function (r) {
				frm.set_value('customer', r.message && r.message.customer ? r.message.customer : '');
			});
		} else {
			frm.set_value('customer', '');
		}
	},

	pickup_date_time(frm) {
		frm.events.calculate_rent(frm);
	},

	delivery_date_time(frm) {
		frm.events.calculate_rent(frm);
	},

	daily_rent(frm) {
		frm.events.calculate_rent(frm);
	},

	calculate_rent(frm) {
		if (!frm.doc.pickup_date_time || !frm.doc.delivery_date_time) return;

		const pickup = frappe.datetime.str_to_obj(frm.doc.pickup_date_time);
		const delivery = frappe.datetime.str_to_obj(frm.doc.delivery_date_time);

		if (delivery <= pickup) {
			frappe.msgprint({
				title: __('Validation Error'),
				indicator: 'red',
				message: __('Delivery Date Time must be after Pickup Date Time.')
			});
			frm.set_value('total_days', 0);
			frm.set_value('total_rent', 0);
			return;
		}

		const diff_ms = delivery - pickup;
		const total_days = Math.ceil(diff_ms / (1000 * 60 * 60 * 24));
		const chargeable_days = Math.max(0, total_days - 7);
		const daily_rent = frm.doc.daily_rent || 0;
		const total_rent = chargeable_days * daily_rent;

		frm.set_value('total_days', total_days);
		frm.set_value('total_rent', total_rent);
		frm.set_value('status', 'Calculated');
	}
});
