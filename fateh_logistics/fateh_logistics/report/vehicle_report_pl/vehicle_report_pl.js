// Copyright (c) 2025, Fateh Logistics and contributors
// For license information, please see license.txt

frappe.query_reports["Vehicle Report PL"] = {
    "filters": [
        {
            "fieldname": "vehicle",
            "label": __("Vehicle"),
            "fieldtype": "MultiSelectList",
            "options": "Vehicle",
            get_data: function(txt) {
                return frappe.db.get_link_options("Vehicle", txt);
            }
        },
        {
            "fieldname": "driver",
            "label": __("Employee"),   
            "fieldtype": "Link",
            "options": "Driver"        
        },
        {
            "fieldname": "job_record",
            "label": __("Job Record"),
            "fieldtype": "MultiSelectList",
            "options": "Job Record",
            get_data: function(txt) {
                return frappe.db.get_link_options("Job Record", txt);
            }
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
    ],

    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

       
        if (column.fieldname === "profit_loss" && data && data.profit_loss !== undefined && data.profit_loss !== null) {
            if (data.profit_loss > 0) {
                value = `<span style="color: #2ecc71; font-weight: 600;">${value}</span>`;
            } else if (data.profit_loss < 0) {
                value = `<span style="color: #e74c3c; font-weight: 600;">${value}</span>`;
            }
        }

        
        if (column.fieldname === "driver" && data && data.driver) {
            value = `<a href="#"
                        style="color: inherit; text-decoration: none;"
                        onclick="frappe.set_route('Form', 'Driver', '${data.driver}'); return false;">
                        ${data.driver}
                     </a>`;
        }

        return value;
    }
};