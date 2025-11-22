

import frappe
from fateh_logistics.api import update_percent_purchased, update_percent_delivered

def update_job_record_percent(doc, method):
    if doc.doctype in ["Purchase Order", "Purchase Invoice", "Purchase Receipt"] and doc.get("custom_job_record"):
        update_percent_purchased(doc.custom_job_record)
    elif doc.doctype in ["Sales Order", "Sales Invoice", "Delivery Note"] and doc.get("custom_job_record"):
        update_percent_delivered(doc.custom_job_record)





