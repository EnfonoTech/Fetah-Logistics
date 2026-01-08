# Copyright (c) 2025, Fateh Logistics and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cstr, strip_html
from erpnext.setup.doctype.vehicle.vehicle import Vehicle as ERPNextVehicle


class Vehicle(ERPNextVehicle):
	def _get_missing_mandatory_fields(self):
		"""Override to skip certain mandatory fields for external vehicles"""
		if self.custom_is_external == "External":
			# For external vehicles, only validate license_plate
			# Get all mandatory fields
			missing = []
			
			# Check only license_plate manually
			license_plate_field = self.meta.get_field("license_plate")
			if license_plate_field and license_plate_field.reqd:
				value = cstr(self.get("license_plate"))
				if not value or not strip_html(value).strip():
					missing.append((
						"license_plate",
						_("Error: Value missing for {0}: {1}").format(
							_(self.doctype), _(license_plate_field.label, context=self.doctype)
						)
					))
			
			return missing
		else:
			# For internal vehicles, use standard validation
			return super()._get_missing_mandatory_fields()

