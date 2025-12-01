import frappe
from frappe import _
from frappe import utils

"""
TODO

Permissions 
- Settings Checbox - Employee can create Expenses
- Add Employee User Permission
Report

More Features - v2
- Alert Approvers - manual - for pending / draft
- Tax Templates
- Separate Request Document
   - Add approved amount on expense entry - auto filled from requested amount but changeable
- Rename App. Expense Voucher vs Expense Entry
- Tests

- Fix
    - Prevent Making JE's before submission / non-approvers

- Add dependant fields
    - Workflow entries
    - JV type: Expense Entry
    - JV Account Reference Type: Expense Entry
    - Mode of Payment: Petty Cash


DONE
  - Issues Fixed
    - Wire Transfer requires reference date, and minor improvements
    - Approver field vanishing
  
  - Print Format improvements - (Not done: Add signatures)
  - Prevent duplicate entry - done
  - Workflow: Pending Approval, Approved (set-approved by)
  - Creation of JV
  - expense refs
  - Roles:
    - Expense Approver
  - Set authorising party

  Add sections to EE and EE Items
    Section: Accounting Dimensions
    - Project
    - Cost Center

  - Add settings fields to Accounts Settings
    Section: Expense Settings
    - Link: Default Payment Account (Link: Mode of Payment) 
      - Desc: Create a Mode of Payment for expenses and link it to your usual expenditure account like Petty Cash
    - Checkbox: Notify all Approvers
      - Desc: when a expense request is made
    - Checkbox: Create Journals Automatically

Add all the fixtures to the app so that it is fully portable
a. Workflows
b. Accounts Settings Fields
c. Fix minor issues
   - Cant set custom print format as default - without customisation

Enhancements
- Added Cost Center Filters
"""


def setup(expense_request, method):
    # add expenses up and set the total field
    # add default project and cost center to expense items

    total = 0
    count = 0
    expense_items = []

    
    for detail in expense_request.expenses:
        total += float(detail.amount)        
        count += 1
        
        if not detail.project and expense_request.default_project:
            detail.project = expense_request.default_project
        
        if not detail.cost_center and expense_request.default_cost_center:
            detail.cost_center = expense_request.default_cost_center

        expense_items.append(detail)

    expense_request.expenses = expense_items

    expense_request.total = total
    expense_request.quantity = count

    make_journal_entry(expense_request)

    


@frappe.whitelist()
def initialise_journal_entry(expense_request_name):
    # make JE from javascript form Make JE button

    make_journal_entry(
        frappe.get_doc('Expense Request', expense_request_name)
    )


def make_journal_entry(expense_request):

    if expense_request.status == "Approved":         

        # check for duplicates
        
        if frappe.db.exists({'doctype': 'Journal Entry', 'bill_no': expense_request.name}):
            frappe.throw(
                title="Error",
                msg="Journal Entry {} already exists.".format(expense_request.name)
            )


        # Preparing the JE: convert expense_request details into je account details

        accounts = []

        for detail in expense_request.expenses:            

            accounts.append({  
                'debit_in_account_currency': float(detail.amount),
                'user_remark': str(detail.description),
                'account': detail.expense_account,
                'project': detail.project,
                'cost_center': detail.cost_center
            })

        # finally add the payment account detail

        pay_account = ""

        if (expense_request.mode_of_payment != "Cash" and (not 
            expense_request.payment_reference or not expense_request.clearance_date)):
            frappe.throw(
                title="Enter Payment Reference",
                msg="Payment Reference and Date are Required for all non-cash payments."
            )
        else:
            expense_request.clearance_date = ""
            expense_request.payment_reference = ""


        pay_account = frappe.db.get_value('Mode of Payment Account', {'parent' : expense_request.mode_of_payment, 'company' : expense_request.company}, 'default_account')
        if not pay_account or pay_account == "":
            frappe.throw(
                title="Error",
                msg="The selected Mode of Payment has no linked account."
            )

        accounts.append({  
            'credit_in_account_currency': float(expense_request.total),
            'user_remark': str(detail.description),
            'account': pay_account,
            'cost_center': expense_request.default_cost_center
        })

        # create the journal entry
        je = frappe.get_doc({
            'title': expense_request.name,
            'doctype': 'Journal Entry',
            'voucher_type': 'Journal Entry',
            'posting_date': expense_request.posting_date,
            'company': expense_request.company,
            'custom_vehicle': expense_request.vehicle,
            'custom_apartment': expense_request.apartment,
            'accounts': accounts,
            'user_remark': expense_request.remarks,
            'mode_of_payment': expense_request.mode_of_payment,
            'cheque_date': expense_request.clearance_date,
            'reference_date': expense_request.clearance_date,
            'cheque_no': expense_request.payment_reference,
            'pay_to_recd_from': expense_request.payment_to,
            'bill_no': expense_request.name
        })

        user = frappe.get_doc("User", frappe.session.user)

        full_name = str(user.first_name) + ' ' + str(user.last_name)
        expense_request.db_set('approved_by', full_name)
        

        je.insert()
        je.submit()


@frappe.whitelist()
def get_remaining_items_from_job(job_record_id, target_doctype):
    """
    Get items from Job Record that have not yet been fully pulled into the given target doctype.
    `target_doctype` must be one of:
        - 'Purchase Order'
        - 'Purchase Invoice'
        - 'Sales Order'
        - 'Sales Invoice'
    """
    if target_doctype not in ['Purchase Order', 'Purchase Invoice', 'Sales Order', 'Sales Invoice', 'Quotation']:
        frappe.throw(_('Unsupported target doctype: {0}').format(target_doctype))

    job = frappe.get_doc("Job Record", job_record_id)
    if not job.items:
        return []

    # Determine target doc's link field to Job Record
    link_field = "custom_job_record"

    # Get existing documents linked to this Job Record
    existing_docs = frappe.get_all(target_doctype, {
        link_field: job_record_id,
        "docstatus": 1
    }, pluck="name")

    # Figure out child table name
    child_table_map = {
        "Purchase Order": "Purchase Order Item",
        "Purchase Invoice": "Purchase Invoice Item",
        "Sales Order": "Sales Order Item",
        "Sales Invoice": "Sales Invoice Item",
        "Quotation": "Quotation Item"
    }

    item_field_map = {
        "item_code": "item_code",
        "qty": "qty"
    }

    item_table = child_table_map.get(target_doctype)
    if not item_table:
        frappe.throw(_('Unknown child table for {0}').format(target_doctype))

    ordered_qty = {}

    if existing_docs:
        item_rows = frappe.get_all(item_table, {
            "parent": ["in", existing_docs]
        }, [item_field_map["item_code"], item_field_map["qty"]])

        for row in item_rows:
            ordered_qty[row.item_code] = ordered_qty.get(row.item_code, 0) + row.qty

    remaining_items = []
    for row in job.items:
        already_ordered = ordered_qty.get(row.item, 0)
        remaining = row.quantity - already_ordered
        if remaining > 0:
            remaining_items.append({
                "item_code": row.item,
                "item_name": row.item_name,
                # "description": row.description,
                "qty": remaining,
                "uom": row.uom,
                "rate": row.rate,
                # "schedule_date": today(),
                # "warehouse": "Stores - " + frappe.db.get_value("Company", job.company, "abbr")
            })

    return remaining_items


@frappe.whitelist()
def get_expense_entries_for_job(job_record_id):
    expense_entries = frappe.get_all(
        "Expense Entry",
        filters={"custom_job_record": job_record_id, "docstatus": 1, "status": "Approved"},
        fields=["name", "total"]
    )

    data = []
    for entry in expense_entries:
        data.append({
            "reference_doctype": "Expense Entry",
            "reference_record": entry.name,
            "amount": entry.total,
        })

    return data


@frappe.whitelist()
def update_percent_purchased(job_record):
    #get all POs under this JR
    pos = frappe.db.get_all("Purchase Order",
        filters={
            "custom_job_record": job_record,
            "status": ["!=", "Cancelled"]},
        fields=['name', 'per_received', 'total_qty'])
    
    total_qty = frappe.db.get_value("Job Record", job_record, 'total_quantity')

    if len(pos) > 0:
        percent = 0
        total = 0
        for po in pos:
            total += po['per_received']*po['total_qty']
        percent = total/total_qty
        frappe.db.set_value('Job Record', job_record, '_received', percent)
    else:
        frappe.db.set_value('Job Record', job_record, '_received', 0)


@frappe.whitelist()
def update_percent_delivered(job_record):
    sos = frappe.db.get_all("Sales Order",
        filters={
            "custom_job_record": job_record,
            "status": ["!=", "Cancelled"]},
        fields=['name', 'per_delivered'])
    
    if len(sos) > 0:
        percent = 0
        total = 0
        for so in sos:
            total += so['per_delivered']
        percent = total/len(sos)
        frappe.db.set_value('Job Record', job_record, '_delivered', percent)
    else:
        frappe.db.set_value('Job Record', job_record, '_delivered', 0)


@frappe.whitelist()
def get_quotations_for_customer(customer):
    if not customer:
        return []

    quotations = frappe.get_all("Quotation",
        filters={
            "docstatus": 1,
            "quotation_to": "Customer",
            "party_name": customer
        },
        fields=["name", "grand_total"],
        order_by="creation desc"
    )
    return quotations


@frappe.whitelist()
def get_items_from_multiple_quotations(quotations):
    import json
    if isinstance(quotations, str):
        quotations = json.loads(quotations)

    items = []
    for quotation in quotations:
        quotation_doc = frappe.get_doc("Quotation", quotation)
        for item in quotation_doc.items:
            items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "uom": item.uom,
                "qty": item.qty,
                "rate": item.rate,
                "amount": item.amount,
                "parent": quotation_doc.name
            })
    return {"items": items}


@frappe.whitelist()
def get_sales_invoices_for_vehicle(vehicle):
    """
    Get all Sales Invoices linked to a vehicle via Sales Invoice Item custom_vehicle field.
    Returns parent Sales Invoice details with totals.
    """
    if not vehicle:
        return []
    
    # Query child table to find parent Sales Invoices
    sales_invoice_items = frappe.get_all(
        "Sales Invoice Item",
        filters={"custom_vehicle": vehicle},
        fields=["parent", "parenttype"],
        distinct=True
    )
    
    if not sales_invoice_items:
        return []
    
    # Get unique parent Sales Invoice names
    sales_invoice_names = [item.parent for item in sales_invoice_items if item.parenttype == "Sales Invoice"]
    
    if not sales_invoice_names:
        return []
    
    # Get parent Sales Invoice details
    sales_invoices = frappe.get_all(
        "Sales Invoice",
        filters={"name": ["in", sales_invoice_names], "docstatus": 1},
        fields=["name", "base_grand_total", "base_total", "outstanding_amount", "currency"]
    )
    
    return sales_invoices


@frappe.whitelist()
def get_purchase_invoices_for_vehicle(vehicle):
    """
    Get all Purchase Invoices linked to a vehicle via Purchase Invoice Item custom_vehicle field.
    Returns parent Purchase Invoice details with totals.
    """
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
    
    # Get parent Purchase Invoice details
    purchase_invoices = frappe.get_all(
        "Purchase Invoice",
        filters={"name": ["in", purchase_invoice_names], "docstatus": 1},
        fields=["name", "base_grand_total", "base_total", "outstanding_amount", "currency"]
    )
    
    return purchase_invoices


@frappe.whitelist()
def get_journal_entries_for_vehicle(vehicle):
    """
    Get all Journal Entries linked to a vehicle via Journal Entry Account custom_vehicle field.
    Returns parent Journal Entry details with total_debit and currency.
    """
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
    journal_entry_names = [item.parent for item in journal_entry_accounts if item.parenttype == "Journal Entry"]
    
    if not journal_entry_names:
        return []
    
    # Get parent Journal Entry details
    journal_entries = frappe.get_all(
        "Journal Entry",
        filters={"name": ["in", journal_entry_names], "docstatus": 1},
        fields=["name", "total_debit", "total_credit", "total_amount_currency"]
    )
    
    return journal_entries


@frappe.whitelist()
def update_driver_allowances(driver_name):
    """
    Sum up allowances from Trip Details and update Driver (only for internal drivers)
    Calculate allowance_taken from Additional Salary records
    Calculate balance (allowance - allowance_taken)
    External drivers don't track allowances - they create Purchase Invoices from Trip Details
    """
    # Check if driver has employee (internal driver) - use db.get_value to avoid loading full doc
    employee = frappe.db.get_value("Driver", driver_name, "employee")
    
    # Only update allowances for internal drivers (those with employee)
    # External drivers don't track allowances
    if not employee:
        return {"status": "info", "message": "Allowance tracking is only for internal drivers"}
    
    # Get all completed trips for this driver
    trips = frappe.get_all(
        "Trip Details",
        filters={
            "driver": driver_name,
            "status": "Trip Completed"
        },
        fields=["name", "allowance"]
    )
    
    # Sum allowances from trips
    total_allowance = sum([trip.allowance or 0 for trip in trips])
    
    # Calculate allowance_taken from Additional Salary records
    # Get all submitted Additional Salary records linked to this driver
    additional_salaries = frappe.get_all(
        "Additional Salary",
        filters={
            "ref_doctype": "Driver",
            "ref_docname": driver_name,
            "docstatus": 1  # Only submitted records
        },
        fields=["name", "amount"]
    )
    
    # Sum amounts from Additional Salary records
    total_allowance_taken = sum([sal.amount or 0 for sal in additional_salaries])
    
    # Update Driver - only update allowance_balance (allowance field doesn't exist)
    # Use frappe.db.set_value to safely set the field
    frappe.db.set_value("Driver", driver_name, "allowance_balance", total_allowance - total_allowance_taken)
    frappe.db.commit()
    
    return {"status": "success", "message": "Allowances updated"}


@frappe.whitelist()
def update_job_assignment_allowances(job_record_name):
    """
    Sum up allowances from Trip Details and update Job Assignment table
    Also calculate balance (allowance - allowance_taken)
    
    This updates allowance fields in the Job Assignment child table based on completed trips
    """
    job_record = frappe.get_doc("Job Record", job_record_name)
    
    # Get all completed trips for this job record
    trips = frappe.get_all(
        "Trip Details",
        filters={
            "job_records": job_record_name,
            "status": "Trip Completed"
        },
        fields=["name", "driver", "allowance"]
    )
    
    # Group by driver and sum allowances
    driver_allowances = {}
    for trip in trips:
        if trip.driver and trip.allowance:
            if trip.driver not in driver_allowances:
                driver_allowances[trip.driver] = 0
            driver_allowances[trip.driver] += trip.allowance
    
    # Update Job Assignment table
    updated = False
    for assignment in job_record.job_assignment:
        if assignment.driver in driver_allowances:
            assignment.allowance = driver_allowances[assignment.driver]
            # Calculate balance
            assignment.allowance_balance = assignment.allowance - (assignment.allowance_taken or 0)
            updated = True
    
    if updated:
        job_record.save()
        return {"status": "success", "message": "Allowances updated"}
    else:
        return {"status": "info", "message": "No allowances to update"}


@frappe.whitelist()
def process_driver_allowance(driver_name, amount=None):
    """
    Process allowance for internal driver (creates Additional Salary)
    Note: External drivers create Purchase Invoice from Trip Details, not from here
    
    Args:
        driver_name: Name of Driver (must have employee linked)
        amount: Amount to process (if None, processes full balance)
    """
    # Check if driver has employee (internal driver) - use db.get_value to avoid loading full doc
    employee = frappe.db.get_value("Driver", driver_name, "employee")
    
    if not employee:
        frappe.throw("This feature is only available for internal drivers (drivers with employee). External drivers should create Purchase Invoice from Trip Details.")
    
    # Calculate current allowance from trips
    trips = frappe.get_all(
        "Trip Details",
        filters={
            "driver": driver_name,
            "status": "Trip Completed"
        },
        fields=["name", "allowance"]
    )
    current_allowance = sum([trip.allowance or 0 for trip in trips])
    
    # Calculate current allowance_taken from Additional Salary records
    additional_salaries = frappe.get_all(
        "Additional Salary",
        filters={
            "ref_doctype": "Driver",
            "ref_docname": driver_name,
            "docstatus": 1  # Only submitted records
        },
        fields=["name", "amount"]
    )
    current_allowance_taken = sum([sal.amount or 0 for sal in additional_salaries])
    
    # Calculate current balance
    current_balance = current_allowance - current_allowance_taken
    
    # Determine amount to process
    if amount is None:
        amount = current_balance
    else:
        amount = float(amount)
    
    if amount <= 0:
        frappe.throw("No allowance amount to process")
    
    # Allow small tolerance for rounding differences (0.01)
    if amount > current_balance + 0.01:
        frappe.throw(f"Amount ({amount}) cannot exceed allowance balance ({current_balance:.2f})")
    
    # If amount is slightly more than balance due to rounding, use balance
    if amount > current_balance:
        amount = current_balance
    
    # Get driver details using db.get_value to avoid loading full document
    # This prevents accessing non-existent fields like allowance_taken
    driver_data = frappe.db.get_value(
        "Driver", 
        driver_name, 
        ["employee", "full_name", "name"], 
        as_dict=True
    )
    
    if not driver_data or not driver_data.employee:
        frappe.throw("Driver must have an employee linked")
    
    # Internal driver - Create Additional Salary
    # Pass driver_name and employee instead of driver object to avoid loading full doc
    result = create_additional_salary_from_driver_data(driver_name, driver_data.employee, driver_data.full_name, amount)
    
    # Update allowance_balance after creating Additional Salary
    # Recalculate allowance_taken (now includes the new Additional Salary)
    new_allowance_taken = current_allowance_taken + amount
    new_allowance_balance = current_allowance - new_allowance_taken
    
    # Update driver with new balance (allowance field doesn't exist, only allowance_balance)
    frappe.db.set_value("Driver", driver_name, "allowance_balance", new_allowance_balance)
    frappe.db.commit()
    
    return result


@frappe.whitelist()
def process_job_assignment_allowance(job_record_name, assignment_idx, amount=None):
    """
    Process allowance for a specific Job Assignment row
    - Internal: Create Additional Salary
    - External: Create Purchase Invoice
    
    DEPRECATED: Use process_driver_allowance instead
    
    Args:
        job_record_name: Name of Job Record
        assignment_idx: Index of Job Assignment row (can be string or int)
        amount: Amount to process (if None, processes full balance)
    """
    # Convert assignment_idx to int if it's a string
    try:
        assignment_idx = int(assignment_idx)
    except (ValueError, TypeError):
        frappe.throw("Invalid assignment index")
    
    job_record = frappe.get_doc("Job Record", job_record_name)
    
    if assignment_idx >= len(job_record.job_assignment):
        frappe.throw("Invalid assignment index")
    
    assignment = job_record.job_assignment[assignment_idx]
    
    if not assignment.driver:
        frappe.throw("Driver is required")
    
    # Determine amount to process
    if amount is None:
        amount = assignment.allowance_balance or assignment.allowance or 0
    else:
        amount = float(amount)
    
    if amount <= 0:
        frappe.throw("No allowance amount to process")
    
    available_balance = (assignment.allowance_balance or assignment.allowance or 0)
    if amount > available_balance:
        frappe.throw("Amount cannot exceed allowance balance")
    
    # Get driver data using db.get_value to avoid loading full document
    driver_employee, driver_full_name, driver_transporter = frappe.db.get_value(
        "Driver", 
        assignment.driver, 
        ["employee", "full_name", "transporter"]
    )
    
    # Check driver type
    if assignment.driver_type == "Own" or driver_employee:
        # Internal driver - Create Additional Salary
        # Create a minimal driver-like object for the function
        driver_data = frappe._dict({
            "employee": driver_employee,
            "full_name": driver_full_name or assignment.driver
        })
        result = create_additional_salary_from_assignment(job_record, assignment, driver_data, amount)
        
        # Update allowance_taken and balance
        assignment.allowance_taken = (assignment.allowance_taken or 0) + amount
        assignment.allowance_balance = (assignment.allowance or 0) - assignment.allowance_taken
        
    else:
        # External driver - Create Purchase Invoice
        if not driver_transporter:
            frappe.throw("External driver must have a transporter linked")
        
        # Create a minimal driver-like object for the function
        driver_data = frappe._dict({
            "transporter": driver_transporter
        })
        result = create_purchase_invoice_from_assignment(job_record, assignment, driver_data, amount)
        
        # Update allowance_taken and balance
        assignment.allowance_taken = (assignment.allowance_taken or 0) + amount
        assignment.allowance_balance = (assignment.allowance or 0) - assignment.allowance_taken
    
    job_record.save()
    
    return result


def create_additional_salary_from_driver_data(driver_name, employee_name, driver_full_name, amount):
    """
    Create Additional Salary for internal driver (from Driver doctype)
    Uses driver_name and employee_name instead of driver object to avoid loading full document
    """
    employee = frappe.get_doc("Employee", employee_name)
    company = getattr(employee, "company", None) or frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company")
    
    # Get or create "Trip Allowance" salary component
    salary_component = "Trip Allowance"
    if not frappe.db.exists("Salary Component", salary_component):
        component = frappe.new_doc("Salary Component")
        component.salary_component = salary_component
        component.type = "Earning"
        component.insert()
    
    # Create Additional Salary
    additional_salary = frappe.new_doc("Additional Salary")
    additional_salary.employee = employee_name
    additional_salary.company = company
    additional_salary.salary_component = salary_component
    additional_salary.amount = amount
    additional_salary.payroll_date = utils.today()
    additional_salary.overwrite_salary_structure_amount = 0
    additional_salary.ref_doctype = "Driver"
    additional_salary.ref_docname = driver_name
    
    # Add description
    additional_salary.description = f"Driver Allowance - {driver_full_name}"
    
    additional_salary.insert()
    additional_salary.submit()
    
    return {
        "status": "success",
        "message": f"Additional Salary {additional_salary.name} created for {amount}",
        "document": additional_salary.name,
        "doctype": "Additional Salary"
    }


def create_additional_salary_from_driver(driver, amount):
    """
    Create Additional Salary for internal driver (from Driver doctype)
    DEPRECATED: Use create_additional_salary_from_driver_data instead to avoid loading full driver doc
    """
    return create_additional_salary_from_driver_data(
        driver.name, 
        driver.employee, 
        driver.full_name, 
        amount
    )


def create_additional_salary_from_assignment(job_record, assignment, driver, amount):
    """
    Create Additional Salary for internal driver (from Job Assignment - DEPRECATED)
    """
    if not driver.employee:
        frappe.throw("Driver must have an employee linked")
    
    employee = frappe.get_doc("Employee", driver.employee)
    company = job_record.company or frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company")
    
    # Get or create "Trip Allowance" salary component
    salary_component = "Trip Allowance"
    if not frappe.db.exists("Salary Component", salary_component):
        component = frappe.new_doc("Salary Component")
        component.salary_component = salary_component
        component.type = "Earning"
        component.insert()
    
    # Create Additional Salary
    additional_salary = frappe.new_doc("Additional Salary")
    additional_salary.employee = driver.employee
    additional_salary.company = company
    additional_salary.salary_component = salary_component
    additional_salary.amount = amount
    additional_salary.payroll_date = utils.today()
    additional_salary.overwrite_salary_structure_amount = 0
    additional_salary.ref_doctype = "Job Record"
    additional_salary.ref_docname = job_record.name
    
    # Add description
    additional_salary.description = f"Driver Allowance - {driver.full_name} - Job {job_record.name}"
    
    additional_salary.insert()
    additional_salary.submit()
    
    return {
        "status": "success",
        "message": f"Additional Salary {additional_salary.name} created for {amount}",
        "document": additional_salary.name,
        "doctype": "Additional Salary"
    }


def create_purchase_invoice_from_driver(driver, amount):
    """
    Create Purchase Invoice for external driver (draft, not submitted)
    - Links Driver in main form
    - Sets rate in item
    """
    if not driver.transporter:
        frappe.throw("External driver must have a transporter linked")
    
    company = frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company")
    posting_date = utils.today()
    
    # Get expense account
    expense_account = frappe.db.get_value(
        "Company", company, "default_expense_account"
    ) or frappe.db.get_value(
        "Account", {"account_type": "Expense Account", "company": company}, "name"
    )
    
    if not expense_account:
        frappe.throw("Please set default expense account for company")
    
    # Get or create service item
    service_item = "Driver Service"
    if not frappe.db.exists("Item", service_item):
        try:
            item = frappe.new_doc("Item")
            item.item_code = service_item
            item.item_name = "Driver Service"
            item.item_group = "Services"
            item.is_stock_item = 0
            item.is_service_item = 1
            item.insert()
        except frappe.DuplicateEntryError:
            # Item was created by another process, just use it
            pass
    
    # Create Purchase Invoice (draft, not submitted)
    pi = frappe.new_doc("Purchase Invoice")
    pi.company = company
    pi.supplier = driver.transporter
    pi.posting_date = posting_date
    # Set Driver in main form (custom_driver field)
    pi.custom_driver = driver.name
    
    # Create item row with rate
    item_row = {
        "item_code": service_item,
        "qty": 1,
        "rate": amount,
        "expense_account": expense_account
    }
    
    pi.append("items", item_row)
    
    pi.set_missing_values()
    pi.insert()
    # Do not submit - return draft document
    
    return {
        "status": "success",
        "message": f"Purchase Invoice {pi.name} created (draft) for {amount}",
        "document": pi.name,
        "doctype": "Purchase Invoice"
    }


def create_purchase_invoice_from_assignment(job_record, assignment, driver, amount):
    """
    Create Purchase Invoice for external driver (draft, not submitted)
    - Links Job Record in main form
    - Links Vehicle in item row
    - Sets rate in item
    
    DEPRECATED: Use create_purchase_invoice_from_driver instead
    """
    if not driver.transporter:
        frappe.throw("External driver must have a transporter linked")
    
    company = job_record.company or frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company")
    posting_date = utils.today()
    
    # Get expense account
    expense_account = frappe.db.get_value(
        "Company", company, "default_expense_account"
    ) or frappe.db.get_value(
        "Account", {"account_type": "Expense Account", "company": company}, "name"
    )
    
    if not expense_account:
        frappe.throw("Please set default expense account for company")
    
    # Get or create service item
    service_item = "Driver Service"
    if not frappe.db.exists("Item", service_item):
        try:
            item = frappe.new_doc("Item")
            item.item_code = service_item
            item.item_name = "Driver Service"
            item.item_group = "Services"
            item.is_stock_item = 0
            item.is_service_item = 1
            item.insert()
        except frappe.DuplicateEntryError:
            # Item was created by another process, just use it
            pass
    
    # Get vehicle from assignment
    vehicle = assignment.vehicle if assignment else None
    
    # Create Purchase Invoice (draft, not submitted)
    pi = frappe.new_doc("Purchase Invoice")
    pi.company = company
    pi.supplier = driver.transporter
    pi.posting_date = posting_date
    # Set Job Record in main form (custom_job_record field)
    pi.custom_job_record = job_record.name
    
    # Create item row with vehicle and rate
    item_row = {
        "item_code": service_item,
        "qty": 1,
        "rate": amount,
        "expense_account": expense_account
    }
    
    # Set vehicle in item row if available
    if vehicle:
        item_row["custom_vehicle"] = vehicle
    
    pi.append("items", item_row)
    
    pi.set_missing_values()
    pi.insert()
    # Do not submit - return draft document
    
    return {
        "status": "success",
        "message": f"Purchase Invoice {pi.name} created (draft) for {amount}",
        "document": pi.name,
        "doctype": "Purchase Invoice"
    }


@frappe.whitelist()
def get_drivers_by_type(doctype, txt, searchfield, start, page_len, filters=None):
    """Filter drivers based on driver_type (Own/External)"""
    # Handle filters - can be passed as dict or string
    if isinstance(filters, str):
        import json
        try:
            filters = json.loads(filters)
        except:
            filters = {}
    
    if not filters:
        filters = {}
    
    # Get driver_type from filters dict
    driver_type = None
    if isinstance(filters, dict):
        driver_type = filters.get("driver_type")
    
    if driver_type == "Own":
        # Own drivers: employee field is not empty and not null
        return frappe.db.sql("""
            SELECT name 
            FROM `tabDriver`
            WHERE employee IS NOT NULL 
            AND employee != ''
            AND name LIKE %(txt)s
            ORDER BY name
            LIMIT %(start)s, %(page_len)s
        """, {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        }, as_list=True)
    elif driver_type == "External":
        # External drivers: employee field is empty or null
        return frappe.db.sql("""
            SELECT name 
            FROM `tabDriver`
            WHERE (employee IS NULL OR employee = '')
            AND name LIKE %(txt)s
            ORDER BY name
            LIMIT %(start)s, %(page_len)s
        """, {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        }, as_list=True)
    else:
        # No filter - return all drivers
        return frappe.get_all(
            "Driver",
            filters={
                "name": ["like", f"%{txt}%"]
            },
            fields=["name"],
            limit_start=start,
            limit_page_length=page_len,
            as_list=True
        )

@frappe.whitelist()
def create_trip_details(job_record, job_assignment, driver, vehicle, trip_amount, allowance=0):

    allowance = float(allowance or 0)
    trip_amount = float(trip_amount or 0)

   
    trip = frappe.new_doc("Trip Details")
    trip.job_records = job_record
    trip.driver = driver
    trip.vehicle = vehicle
    trip.trip_amount = trip_amount
    trip.allowance = allowance
    trip.status = "Created"
    trip.insert(ignore_permissions=True)

    frappe.db.set_value("Job Assignment", job_assignment, "trip_detail_status", "Created")


    # Get driver data using db.get_value to avoid loading full document
    driver_employee, driver_transporter = frappe.db.get_value(
        "Driver", 
        driver, 
        ["employee", "transporter"]
    )

    if not driver_employee:

        if not driver_transporter:
            frappe.throw("Transporter not linked in Driver master.")

        ITEM = "Service Transportation"
        supplier = driver_transporter
        company = frappe.defaults.get_user_default("Company")

       
        pi = frappe.new_doc("Purchase Invoice")
        pi.company = company
        pi.supplier = supplier
        pi.posting_date = frappe.utils.today()
        pi.bill_date = frappe.utils.today()
        pi.custom_job_record = trip.job_records

        pi.append("items", {
            "item_code": ITEM,
            "qty": 1,
            "rate": allowance,
            "amount": allowance
        })

        pi.insert(ignore_permissions=True)

        frappe.db.set_value("Purchase Invoice", pi.name, "custom_trip_details", trip.name, update_modified=False)
        frappe.db.set_value("Trip Details", trip.name, "custom_purchase_invoice", pi.name, update_modified=False)
        frappe.db.set_value("Trip Details", trip.name, "custom_purchase_invoice_status", "Created", update_modified=False)


    return {
        "trip_name": trip.name
    }
