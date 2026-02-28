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
            "width": 130
        },
        {
            "fieldname": "job_record",
            "label": _("Job Record"),
            "fieldtype": "Link",
            "options": "Job Record",
            "width": 140
        },
        {
            "fieldname": "driver",
            "label": _("Employee"),
            "fieldtype": "Link",
            "options": "Driver",
            "width": 160
        },
        {
            "fieldname": "total_credit",
            "label": _("Trip Credit"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "vehicle_total_credit",
            "label": _("Total Credit"),
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "fieldname": "journal_entry",
            "label": _("Journal Entry"),
            "fieldtype": "Link",
            "options": "Journal Entry",
            "width": 160
        },
        {
            "fieldname": "account",
            "label": _("Account"),
            "fieldtype": "Link",
            "options": "Account",
            "width": 200
        },
        {
            "fieldname": "je_debit",
            "label": _("JE Debit"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "total_debit",
            "label": _("Total Debit"),
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "fieldname": "profit_loss",
            "label": _("Profit & Loss"),
            "fieldtype": "Currency",
            "width": 130
        }
    ]


def parse_multivalue(value):
    if not value:
        return []
    if isinstance(value, list):
        return [v.strip() for v in value if v.strip()]
    return [v.strip() for v in str(value).split(",") if v.strip()]


def get_data(filters):
    from_date = filters.get("from_date")
    to_date   = filters.get("to_date")

    vehicle_filter    = parse_multivalue(filters.get("vehicle"))
    driver_filter     = parse_multivalue(filters.get("driver")) 
    job_record_filter = parse_multivalue(filters.get("job_record"))

   
    jr_filters = {"docstatus": ["<", 2]}
    if from_date and to_date:
        jr_filters["date"] = ["between", [from_date, to_date]]
    elif from_date:
        jr_filters["date"] = [">=", from_date]
    elif to_date:
        jr_filters["date"] = ["<=", to_date]

    if job_record_filter:
        jr_filters["name"] = job_record_filter[0] if len(job_record_filter) == 1 else ["in", job_record_filter]

    job_records = frappe.get_all("Job Record", filters=jr_filters, fields=["name", "date"])
    if not job_records:
        return []

    jr_names = [jr.name for jr in job_records]
    jr_date_map = {jr.name: jr.date for jr in job_records}

    #Job Assignments
    ja_filters = {"parent": ["in", jr_names], "parenttype": "Job Record"}

    if vehicle_filter:
        ja_filters["vehicle"] = vehicle_filter[0] if len(vehicle_filter) == 1 else ["in", vehicle_filter]

    if driver_filter:
        ja_filters["driver"] = driver_filter[0] if len(driver_filter) == 1 else ["in", driver_filter]

    job_assignments = frappe.get_all(
        "Job Assignment",
        filters=ja_filters,
        fields=["parent", "vehicle", "driver", "driver_name", "driver_type", "trip_amount"]
    )
    if not job_assignments:
        return []

    vehicles_in_report = list({ja.get("vehicle") for ja in job_assignments if ja.get("vehicle")})

    #Purchase Invoice debit per vehicle
    pi_debit_map = {}
    pi_date_filter = {"docstatus": 1}
    if from_date and to_date:
        pi_date_filter["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        pi_date_filter["posting_date"] = [">=", from_date]
    elif to_date:
        pi_date_filter["posting_date"] = ["<=", to_date]

    pi_list = frappe.get_all("Purchase Invoice", filters=pi_date_filter, fields=["name"])
    if pi_list:
        pi_names = [p.name for p in pi_list]
        pi_items = frappe.get_all(
            "Purchase Invoice Item",
            filters={
                "parent": ["in", pi_names],
                "parenttype": "Purchase Invoice",
                "custom_vehicle": ["in", vehicles_in_report]
            },
            fields=["custom_vehicle", "base_amount", "amount"]
        )
        for item in pi_items:
            v = item.custom_vehicle
            pi_debit_map[v] = pi_debit_map.get(v, 0) + (item.base_amount or item.amount or 0)

    #Journal Entry detail per vehicle
    je_detail_map = {}
    je_used_vehicles = set()

    je_date_filter = {"docstatus": 1}
    if from_date and to_date:
        je_date_filter["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        je_date_filter["posting_date"] = [">=", from_date]
    elif to_date:
        je_date_filter["posting_date"] = ["<=", to_date]

    je_list = frappe.get_all("Journal Entry", filters=je_date_filter, fields=["name"])
    if je_list:
        je_names = [j.name for j in je_list]
        je_names_fmt   = ", ".join(frappe.db.escape(n) for n in je_names)
        vehicles_fmt   = ", ".join(frappe.db.escape(v) for v in vehicles_in_report)
        je_accounts = frappe.db.sql("""
            SELECT
                parent,
                custom_vehicle,
                account,
                debit,
                debit_in_account_currency
            FROM `tabJournal Entry Account`
            WHERE
                parenttype = 'Journal Entry'
                AND parent IN ({je_names})
                AND custom_vehicle IN ({vehicles})
        """.format(je_names=je_names_fmt, vehicles=vehicles_fmt), as_dict=True)
        for acc in je_accounts:
            v = acc.custom_vehicle
            debit_amt = acc.debit or acc.debit_in_account_currency or 0
            if debit_amt <= 0:
                continue
            if v not in je_detail_map:
                je_detail_map[v] = []
            je_detail_map[v].append({
                "journal_entry": acc.parent,
                "account":       acc.account,
                "je_debit":      debit_amt
            })

    #sum of all trip_amounts
    vehicle_total_credit_map = {}
    for ja in job_assignments:
        v = ja.get("vehicle") or ""
        vehicle_total_credit_map[v] = vehicle_total_credit_map.get(v, 0) + (ja.get("trip_amount") or 0)

    #Build report rows
   
    job_assignments = sorted(job_assignments, key=lambda x: (x.get('vehicle') or '', jr_date_map.get(x.get('parent'), '')))

    data = []
    vehicle_first_row = set()

    for ja in job_assignments:
        vehicle      = ja.get("vehicle") or ""
        driver_id    = ja.get("driver") or ""
        driver_name  = ja.get("driver_name") or ""
        total_credit = ja.get("trip_amount") or 0
        pi_debit     = pi_debit_map.get(vehicle, 0)

        je_rows  = je_detail_map.get(vehicle, []) if vehicle not in je_used_vehicles else []
        je_total = sum(r["je_debit"] for r in je_detail_map.get(vehicle, []))
        total_debit  = pi_debit + je_total
        profit_loss  = total_credit - total_debit

        is_first = vehicle not in vehicle_first_row
        if is_first:
            vehicle_first_row.add(vehicle)

        if je_rows:
            je_used_vehicles.add(vehicle)
            first_je = je_rows[0]
            data.append({
                "vehicle":              vehicle,
                "job_record":           ja.get("parent"),
                "driver":               driver_id,
                "driver_name":          driver_name,
                "total_credit":         total_credit,
                "vehicle_total_credit": vehicle_total_credit_map.get(vehicle, 0) if is_first else None,
                "journal_entry":        first_je["journal_entry"],
                "account":              first_je["account"],
                "je_debit":             first_je["je_debit"],
                "total_debit":          total_debit if is_first else None,
                "profit_loss":          profit_loss if is_first else None
            })
            for je_row in je_rows[1:]:
                data.append({
                    "vehicle":              "",
                    "job_record":           "",
                    "driver":               "",
                    "driver_name":          "",
                    "total_credit":         None,
                    "vehicle_total_credit": None,
                    "journal_entry":        je_row["journal_entry"],
                    "account":              je_row["account"],
                    "je_debit":             je_row["je_debit"],
                    "total_debit":          None,
                    "profit_loss":          None
                })
        else:
            data.append({
                "vehicle":              vehicle,
                "job_record":           ja.get("parent"),
                "driver":               driver_id,
                "driver_name":          driver_name,
                "total_credit":         total_credit,
                "vehicle_total_credit": vehicle_total_credit_map.get(vehicle, 0) if is_first else None,
                "journal_entry":        "",
                "account":              "",
                "je_debit":             None,
                "total_debit":          total_debit if is_first else None,
                "profit_loss":          profit_loss if is_first else None
            })

    return data