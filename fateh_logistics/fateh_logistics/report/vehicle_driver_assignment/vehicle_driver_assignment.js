// Copyright (c) 2025, Fateh Logistics and contributors
// For license information, please see license.txt

frappe.query_reports["Vehicle Driver Assignment"] = {
    "filters": [
        {
            "fieldname": "vehicle",
            "label": __("Vehicle"),
            "fieldtype": "Link",
            "options": "Vehicle"
        },
        {
            "fieldname": "driver",
            "label": __("Driver"),
            "fieldtype": "Link",
            "options": "Driver"
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        }
    ]
};


