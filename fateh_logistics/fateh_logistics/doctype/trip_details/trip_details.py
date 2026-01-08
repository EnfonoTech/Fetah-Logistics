# Copyright (c) 2025, siva and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from fateh_logistics.api import update_driver_allowances, update_job_assignment_allowances
from frappe.utils import today


@frappe.whitelist()
def make_purchase_invoice(source_name, target_doc=None):
	"""
	Create Purchase Invoice from Trip Details for external drivers
	"""
	source = frappe.get_doc("Trip Details", source_name)
	
	# Get driver details
	if not source.driver:
		frappe.throw("Driver is required to create Purchase Invoice")
	
	# Get driver transporter using db.get_value to avoid loading full doc
	transporter = frappe.db.get_value("Driver", source.driver, "transporter")
	
	# Check if driver is external (has transporter, no employee)
	if not transporter:
		frappe.throw("Purchase Invoice can only be created for external drivers (drivers with transporter)")
	
	# Get company
	company = frappe.defaults.get_user_default("company") or \
		frappe.db.get_single_value("Global Defaults", "default_company")
	
	if not company:
		frappe.throw("Please set default company")
	
	# Create Purchase Invoice directly
	pi = frappe.new_doc("Purchase Invoice")
	
	# Set basic fields FIRST
	pi.company = company
	pi.supplier = transporter
	pi.posting_date = today()
	
	# Set custom fields
	pi.custom_job_record = source.job_records
	pi.custom_trip_details = source.name
	
	# Append first row with rate from allowance (no item selected - user will select)
	if source.allowance:
		pi.append("items", {
			"qty": 1,
			"rate": source.allowance or 0
		})
	
	# Call set_missing_values to populate dependent fields like credit_to, etc.
	pi.set_missing_values()
	
	# Return the document (as draft, not inserted)
	return pi


class TripDetails(Document):
	def before_save(self):
		"""Auto-update driver and job assignment allowances when trip is completed (only for internal drivers)"""
		if self.status == "Trip Completed" and self.driver and self.allowance:
			# Check if driver is internal (has employee) before updating - use db.get_value to avoid loading full doc
			employee = frappe.db.get_value("Driver", self.driver, "employee")
			if employee:
				# Update driver allowance synchronously when trip is completed
				try:
					update_driver_allowances(self.driver)
				except Exception:
					# Log error but don't block save
					frappe.log_error(frappe.get_traceback(), "Error updating driver allowances for Trip Details")
			
			# Update Job Assignment allowances if job_records is linked
			if self.job_records:
				try:
					update_job_assignment_allowances(self.job_records)
				except Exception:
					# Log error but don't block save
					frappe.log_error(frappe.get_traceback(), "Error updating job assignment allowances for Trip Details")
	
	def after_insert(self):
		"""Auto-update driver and job assignment allowances when trip is created with allowance (only for internal drivers)"""
		if self.driver and self.allowance:
			# Check if driver is internal (has employee) before updating - use db.get_value to avoid loading full doc
			employee = frappe.db.get_value("Driver", self.driver, "employee")
			if employee:
				# Update driver allowance in background
				frappe.enqueue(
					"fateh_logistics.api.update_driver_allowances",
					driver_name=self.driver,
					queue="short"
				)
			
			# Update Job Assignment allowances if job_records is linked
			if self.job_records:
				frappe.enqueue(
					"fateh_logistics.api.update_job_assignment_allowances",
					job_record_name=self.job_records,
					queue="short"
				)
	
	def on_update(self):
		"""Update driver and job assignment allowances when trip allowance or status is changed (only for internal drivers)"""
		if self.driver:
			# Update if allowance changed or status changed to completed
			should_update = (self.has_value_changed("allowance") or 
				(self.has_value_changed("status") and self.status == "Trip Completed"))
			
			if should_update:
				# Check if driver is internal (has employee) before updating - use db.get_value to avoid loading full doc
				employee = frappe.db.get_value("Driver", self.driver, "employee")
				if employee:
					# Update driver allowance in background
					frappe.enqueue(
						"fateh_logistics.api.update_driver_allowances",
						driver_name=self.driver,
						queue="short"
					)
				
				# Update Job Assignment allowances - handle both old and new job_records if changed
				job_records_to_update = []
				if self.job_records:
					job_records_to_update.append(self.job_records)
				
				# If job_records changed, also update the old one
				if self.has_value_changed("job_records") and self.get_doc_before_save():
					old_job_records = self.get_doc_before_save().job_records
					if old_job_records and old_job_records != self.job_records:
						job_records_to_update.append(old_job_records)
				
				# Update all relevant job records
				for job_record_name in job_records_to_update:
					frappe.enqueue(
						"fateh_logistics.api.update_job_assignment_allowances",
						job_record_name=job_record_name,
						queue="short"
					)

