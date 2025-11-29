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
    
    # Build Trip Details filter based on vehicle assignment
    trip_filter = {"docstatus": ["!=", 2]}
    if filters.get("vehicle"):
        trip_filter["vehicle"] = filters.get("vehicle")
    
    # Add date filter
    if from_date and to_date:
        trip_filter["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        trip_filter["posting_date"] = [">=", from_date]
    elif to_date:
        trip_filter["posting_date"] = ["<=", to_date]
    
    # Get unique vehicles from Trip Details
    trip_details = frappe.get_all(
        "Trip Details",
        filters=trip_filter,
        fields=["vehicle"],
        distinct=True
    )
    
    # Get unique vehicle names
    vehicle_names = list(set([trip.vehicle for trip in trip_details if trip.vehicle]))
    
    if not vehicle_names:
        return []
    
    # Get vehicle details
    vehicles = frappe.get_all(
        "Vehicle",
        filters={"name": ["in", vehicle_names]},
        fields=["name", "license_plate", "employee"]
    )
    
    # Apply employee filter if specified
    if filters.get("employee"):
        vehicles = [v for v in vehicles if v.employee == filters.get("employee")]
    
    data = []
    
    for vehicle in vehicles:
        vehicle_name = vehicle.name
        
        # Get Trip Details Revenue (Income from Trip Details)
        trip_revenue = get_trip_revenue_for_vehicle(vehicle_name, from_date, to_date)
        total_credit = trip_revenue
        
        # Get Purchase Invoices (part of Total Debit)
        purchase_invoices = get_purchase_invoices_for_vehicle(vehicle_name, from_date, to_date)
        total_purchase = sum([inv.get("base_total", 0) or 0 for inv in purchase_invoices])
        
        # Get Journal Entries (part of Total Debit)
        journal_entries = get_journal_entries_for_vehicle(vehicle_name, from_date, to_date)
        total_journal = sum([entry.get("total_debit", 0) or 0 for entry in journal_entries])
        
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


def get_purchase_invoices_for_vehicle(vehicle, from_date=None, to_date=None):
    """Get Purchase Invoices linked to vehicle via Purchase Invoice Item"""
    if not vehicle:
        return []
    
    # Query child table to find parent Purchase Invoices
    purchase_invoice_items = frappe.get_all(
        "Purchase Invoice Item",
        filters={"custom_vehicle": vehicle},
        fields=["parent", "parenttype"],
        distinct=True
    )
    
    if not purchase_invoice_items:
        return []
    
    # Get unique parent Purchase Invoice names
    purchase_invoice_names = [item.parent for item in purchase_invoice_items if item.parenttype == "Purchase Invoice"]
    
    if not purchase_invoice_names:
        return []
    
    # Build date filter
    date_filter = {"name": ["in", purchase_invoice_names], "docstatus": 1}
    if from_date and to_date:
        date_filter["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        date_filter["posting_date"] = [">=", from_date]
    elif to_date:
        date_filter["posting_date"] = ["<=", to_date]
    
    # Get parent Purchase Invoice details
    purchase_invoices = frappe.get_all(
        "Purchase Invoice",
        filters=date_filter,
        fields=["name", "base_grand_total", "base_total", "outstanding_amount", "currency", "posting_date"]
    )
    
    return purchase_invoices


def get_journal_entries_for_vehicle(vehicle, from_date=None, to_date=None):
    """Get Journal Entries linked to vehicle via Journal Entry Account"""
    if not vehicle:
        return []
    
    # Query child table to find parent Journal Entries
    journal_entry_accounts = frappe.get_all(
        "Journal Entry Account",
        filters={"custom_vehicle": vehicle},
        fields=["parent", "parenttype"],
        distinct=True
    )
    
    if not journal_entry_accounts:
        return []
    
    # Get unique parent Journal Entry names
    journal_entry_names = [acc.parent for acc in journal_entry_accounts if acc.parenttype == "Journal Entry"]
    
    if not journal_entry_names:
        return []
    
    # Build date filter
    date_filter = {"name": ["in", journal_entry_names], "docstatus": 1}
    if from_date and to_date:
        date_filter["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        date_filter["posting_date"] = [">=", from_date]
    elif to_date:
        date_filter["posting_date"] = ["<=", to_date]
    
    # Get parent Journal Entry details
    journal_entries = frappe.get_all(
        "Journal Entry",
        filters=date_filter,
        fields=["name", "total_debit", "total_credit", "total_amount_currency", "posting_date"]
    )
    
    return journal_entries


def get_trip_revenue_for_vehicle(vehicle, from_date=None, to_date=None):
    """Get Vehicle Revenue from Trip Details"""
    if not vehicle:
        return 0
    
    # Build date filter
    date_filter = {"vehicle": vehicle, "docstatus": ["!=", 2]}
    if from_date and to_date:
        date_filter["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        date_filter["posting_date"] = [">=", from_date]
    elif to_date:
        date_filter["posting_date"] = ["<=", to_date]
    
    # Get Trip Details with vehicle_revenue
    trip_details = frappe.get_all(
        "Trip Details",
        filters=date_filter,
        fields=["name", "vehicle_revenue", "posting_date"]
    )
    
    # Sum up vehicle_revenue
    total_revenue = sum([trip.get("vehicle_revenue", 0) or 0 for trip in trip_details])
    
    return total_revenue

