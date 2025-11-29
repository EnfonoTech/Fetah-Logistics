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
            "fieldname": "driver",
            "label": _("Driver"),
            "fieldtype": "Link",
            "options": "Driver",
            "width": 200
        },
        {
            "fieldname": "driver_name",
            "label": _("Driver Name"),
            "fieldtype": "Data",
            "width": 250
        },
        {
            "fieldname": "vehicle",
            "label": _("Vehicle"),
            "fieldtype": "Link",
            "options": "Vehicle",
            "width": 200
        },
        {
            "fieldname": "posting_date",
            "label": _("Posting Date"),
            "fieldtype": "Date",
            "width": 150
        },
        {
            "fieldname": "trip_details",
            "label": _("Trip Details"),
            "fieldtype": "Link",
            "options": "Trip Details",
            "width": 200
        }
    ]


def get_data(filters):
    # Build Trip Details filter
    trip_filter = {"docstatus": ["!=", 2]}
    
    # Vehicle filter
    if filters.get("vehicle"):
        trip_filter["vehicle"] = filters.get("vehicle")
    
    # Driver filter
    if filters.get("driver"):
        trip_filter["driver"] = filters.get("driver")
    
    # Date filter - using posting_date
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    if from_date and to_date:
        trip_filter["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        trip_filter["posting_date"] = [">=", from_date]
    elif to_date:
        trip_filter["posting_date"] = ["<=", to_date]
    
    # Get Trip Details - only vehicles and drivers that are assigned
    trip_details = frappe.get_all(
        "Trip Details",
        filters=trip_filter,
        fields=[
            "name",
            "posting_date",
            "vehicle",
            "driver"
        ],
        order_by="driver, posting_date desc, vehicle"
    )
    
    data = []
    
    for trip in trip_details:
        # Only include trips that have both vehicle and driver assigned
        if not trip.vehicle or not trip.driver:
            continue
            
        # Get driver name
        driver_name = ""
        if trip.driver:
            try:
                driver_doc = frappe.get_cached_doc("Driver", trip.driver)
                driver_name = driver_doc.full_name or trip.driver
            except:
                driver_name = trip.driver
        
        data.append({
            "driver": trip.driver,
            "driver_name": driver_name,
            "vehicle": trip.vehicle,
            "posting_date": trip.posting_date,
            "trip_details": trip.name
        })
    
    return data

