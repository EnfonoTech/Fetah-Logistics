# Copyright (c) 2025, ramees@enfono.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "name", "label": _("ID"), "fieldtype": "Link", "options": "Job Record", "width": 180},
        {"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 100},
        {"fieldname": "job_type", "label": _("Job Type"), "fieldtype": "Data", "width": 120},
        {"fieldname": "custom_branch", "label": _("Branch"), "fieldtype": "Data", "width": 120},
        {"fieldname": "current_operational_status", "label": _("Current Operational Status"), "fieldtype": "Data", "width": 180},
        {"fieldname": "job_status", "label": _("Job Status"), "fieldtype": "Data", "width": 120},
        {"fieldname": "custom_customer_name", "label": _("Customer Name"), "fieldtype": "Data", "width": 180},
        {"fieldname": "custom_place_of_delivery", "label": _("Place of Delivery"), "fieldtype": "Data", "width": 180},
        {"fieldname": "custom_place_of_receipt", "label": _("Place of Receipt"), "fieldtype": "Data", "width": 180},
        {"fieldname": "custom_eta", "label": _("ETA"), "fieldtype": "Datetime", "width": 150},
        {"fieldname": "custom_etd", "label": _("ETD"), "fieldtype": "Datetime", "width": 150},
        {"fieldname": "custom_created_by", "label": _("Created By"), "fieldtype": "Link", "options": "User", "width": 140},
        {"fieldname": "custom_sales_executive", "label": _("Sales Executive"), "fieldtype": "Data", "width": 150},
        {"fieldname": "custom_attentions", "label": _("Attention"), "fieldtype": "Data", "width": 150}
    ]


def get_data(filters=None):
    if not filters:
        filters = {}
    
    results = frappe.get_all(
        'Job Record',
        fields=[
            'name', 'date', 'job_type', 'custom_branch', 'current_operational_status',
            'job_status', 'custom_customer_name', 'custom_place_of_delivery',
            'custom_place_of_receipt', 'custom_eta', 'custom_etd', 'custom_created_by',
            'custom_sales_executive', 'custom_attentions'
        ],
        filters={
            "docstatus": ["<", 2], 
            "date": ["between", [filters.get("from_date"), filters.get("to_date")]]
        },
        order_by="date DESC"
    )
    
    return results
