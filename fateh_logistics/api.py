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





