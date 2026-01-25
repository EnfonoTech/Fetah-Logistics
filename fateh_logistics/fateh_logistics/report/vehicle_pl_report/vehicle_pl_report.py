# Copyright (c) 2025, Fateh Logistics and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "vehicle",
            "label": _("Vehicle"),
            "fieldtype": "Link",
            "options": "Vehicle",
            "width": 250
        },
        {
            "fieldname": "employee",
            "label": _("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 250
        },
        {
            "fieldname": "total_credit",
            "label": _("Total Credit"),
            "fieldtype": "Currency",
            "width": 250
        },
        {
            "fieldname": "total_debit",
            "label": _("Total Debit"),
            "fieldtype": "Currency",
            "width": 250
        },
        {
            "fieldname": "profit_loss",
            "label": _("Profit & Loss"),
            "fieldtype": "Currency",
            "width": 250
        }
    ]


def get_data(filters):
    # Date filters
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    # Get all Internal vehicles first
    vehicle_filter = {"custom_is_external": "Internal"}
    if filters.get("vehicle"):
        vehicle_filter["name"] = filters.get("vehicle")
    
    # Get vehicle details - only Internal vehicles
    vehicles = frappe.get_all(
        "Vehicle",
        filters=vehicle_filter,
        fields=["name", "license_plate", "employee"]
    )
    
    # Apply employee filter if specified
    if filters.get("employee"):
        vehicles = [v for v in vehicles if v.employee == filters.get("employee")]
    
    if not vehicles:
        return []
    
    data = []
    
    for vehicle in vehicles:
        vehicle_name = vehicle.name
        
        # Get Total Credit from job_assignment trip_amount
        total_credit = get_trip_amount_from_job_assignment(vehicle_name, from_date, to_date)
        
        # Get Purchase Invoices (part of Total Debit) - only sum rows with vehicle
        total_purchase = get_purchase_invoice_amount_for_vehicle(vehicle_name, from_date, to_date)
        
        # Get Journal Entries (part of Total Debit) - only sum rows with vehicle
        total_journal = get_journal_entry_amount_for_vehicle(vehicle_name, from_date, to_date)
        
        total_debit = total_purchase + total_journal
        profit_loss = total_credit - total_debit
        
        # Get employee - store the ID (name) for proper linking and get name for display
        employee_id = vehicle.employee or ""
        employee_name = ""
        if employee_id:
            try:
                employee_doc = frappe.get_doc("Employee", employee_id)
                employee_name = employee_doc.employee_name or employee_id
            except:
                employee_name = employee_id
        
        data.append({
            "vehicle": vehicle_name,
            "employee": employee_id,  # Use employee ID (name) for proper linking
            "employee_name": employee_name,  # Store employee name for display
            "total_credit": total_credit,
            "total_debit": total_debit,
            "profit_loss": profit_loss
        })
    
    return data


def get_purchase_invoice_amount_for_vehicle(vehicle, from_date=None, to_date=None):
    """Get sum of Purchase Invoice Item amounts where vehicle matches"""
    if not vehicle:
        return 0
    
    # Build date filter for parent Purchase Invoices
    date_filter = {"docstatus": 1}
    if from_date and to_date:
        date_filter["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        date_filter["posting_date"] = [">=", from_date]
    elif to_date:
        date_filter["posting_date"] = ["<=", to_date]
    
    # Get all Purchase Invoices in date range
    purchase_invoices = frappe.get_all(
        "Purchase Invoice",
        filters=date_filter,
        fields=["name"]
    )
    
    if not purchase_invoices:
        return 0
    
    purchase_invoice_names = [pi.name for pi in purchase_invoices]
    
    # Get Purchase Invoice Items where vehicle matches and parent is in date range
    purchase_invoice_items = frappe.get_all(
        "Purchase Invoice Item",
        filters={
            "custom_vehicle": vehicle,
            "parent": ["in", purchase_invoice_names],
            "parenttype": "Purchase Invoice"
        },
        fields=["amount", "base_amount"]
    )
    
    # Sum only the amounts of items where vehicle matches
    total_amount = sum([item.get("base_amount", 0) or item.get("amount", 0) or 0 for item in purchase_invoice_items])
    
    return total_amount


def get_journal_entry_amount_for_vehicle(vehicle, from_date=None, to_date=None):
    """Get sum of Journal Entry Account debit amounts where vehicle matches"""
    if not vehicle:
        return 0
    
    # Build date filter for parent Journal Entries
    date_filter = {"docstatus": 1}
    if from_date and to_date:
        date_filter["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        date_filter["posting_date"] = [">=", from_date]
    elif to_date:
        date_filter["posting_date"] = ["<=", to_date]
    
    # Get all Journal Entries in date range
    journal_entries = frappe.get_all(
        "Journal Entry",
        filters=date_filter,
        fields=["name"]
    )
    
    if not journal_entries:
        return 0
    
    journal_entry_names = [je.name for je in journal_entries]
    
    # Get Journal Entry Accounts where vehicle matches and parent is in date range
    journal_entry_accounts = frappe.get_all(
        "Journal Entry Account",
        filters={
            "custom_vehicle": vehicle,
            "parent": ["in", journal_entry_names],
            "parenttype": "Journal Entry"
        },
        fields=["debit", "debit_in_account_currency"]
    )
    
    # Sum only the debit amounts of accounts where vehicle matches
    total_debit = sum([acc.get("debit", 0) or acc.get("debit_in_account_currency", 0) or 0 for acc in journal_entry_accounts])
    
    return total_debit


def get_trip_amount_from_job_assignment(vehicle, from_date=None, to_date=None):
    """Get sum of trip_amount from job_assignment table for the vehicle"""
    if not vehicle:
        return 0
    
    # Build date filter for Job Record
    date_filter = {"docstatus": ["<", 2]}
    if from_date and to_date:
        date_filter["date"] = ["between", [from_date, to_date]]
    elif from_date:
        date_filter["date"] = [">=", from_date]
    elif to_date:
        date_filter["date"] = ["<=", to_date]
    
    # Get all Job Records in date range
    job_records = frappe.get_all(
        "Job Record",
        filters=date_filter,
        fields=["name"]
    )
    
    if not job_records:
        return 0
    
    job_record_names = [jr.name for jr in job_records]
    
    # Get job_assignment rows where vehicle matches
    job_assignments = frappe.get_all(
        "Job Assignment",
        filters={
            "vehicle": vehicle,
            "parent": ["in", job_record_names],
            "parenttype": "Job Record"
        },
        fields=["trip_amount"]
    )
    
    # Sum up trip_amount
    total_trip_amount = sum([ja.get("trip_amount", 0) or 0 for ja in job_assignments])
    
    return total_trip_amount

