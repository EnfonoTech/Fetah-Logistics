// Copyright (c) 2025, Fateh Logistics and contributors
// For license information, please see license.txt

frappe.query_reports["Vehicle PL Report"] = {
    "filters": [
        {
            "fieldname": "vehicle",
            "label": __("Vehicle"),
            "fieldtype": "Link",
            "options": "Vehicle"
        },
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee"
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
        
        // Color code Profit & Loss column
        if (column.id === "profit_loss" && data && data.profit_loss !== undefined) {
            if (data.profit_loss > 0) {
                // Green for profit
                value = `<span style="color: green;">${value}</span>`;
            } else if (data.profit_loss < 0) {
                // Red for loss
                value = `<span style="color: red;">${value}</span>`;
            }
        }
        
        return value;
    }
};

