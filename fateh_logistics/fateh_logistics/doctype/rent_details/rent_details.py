# Copyright (c) 2026, ramees@enfono.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RentDetails(Document):
	def validate(self):
		if self.project and not self.customer:
			self.customer = frappe.db.get_value("Project", self.project, "customer")


@frappe.whitelist()
def make_sales_invoice(source_name):
	doc = frappe.get_doc("Rent Details", source_name)

	if not doc.customer and doc.project:
		doc.customer = frappe.db.get_value("Project", doc.project, "customer")

	if not doc.customer:
		frappe.throw("Customer is required to create a Sales Invoice. Please link a Project with a customer.")

	if not doc.total_rent or doc.total_rent <= 0:
		frappe.throw("Total Rent must be greater than 0 to create a Sales Invoice.")

	if doc.sales_invoice:
		frappe.throw("Sales Invoice {0} already created for this record.".format(doc.sales_invoice))

	si = frappe.new_doc("Sales Invoice")
	si.customer = doc.customer
	si.project = doc.project

	chargeable_days = max(0, (doc.total_days or 0) - 7)

	si.append("items", {
		"item_code": doc.rent_item,
		"qty": 1,
		"rate": doc.total_rent,
		"description": "Container Rent - {0} chargeable days".format(chargeable_days),
		"uom": "Nos"
	})

	si.insert(ignore_permissions=True)
	frappe.db.set_value("Rent Details", source_name, {
		"sales_invoice": si.name,
		"status": "Invoiced"
	})

	return si.name
