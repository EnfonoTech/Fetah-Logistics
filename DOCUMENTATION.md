# Fateh Logistics - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Core Concepts](#core-concepts)
4. [Key Doctypes](#key-doctypes)
5. [Workflows](#workflows)
6. [APIs](#apis)
7. [Features](#features)
8. [Customizations](#customizations)
9. [Reports](#reports)
10. [Usage Examples](#usage-examples)
11. [Troubleshooting](#troubleshooting)

---

## Overview

**Fateh Logistics** is a comprehensive logistics management module built on Frappe Framework/ERPNext. It provides end-to-end logistics operations management including job tracking, warehouse management, transportation, customs clearance, and financial tracking.

### Key Capabilities
- **Job Record Management**: Central tracking of all logistics jobs
- **Multi-type Logistics Operations**: Transportation, Warehouse, Packing, Crating, Customs Clearance, Terminal Handling
- **Integration with ERPNext**: Seamless integration with Sales, Purchase, and Accounting modules
- **Expense Tracking**: Complete expense management with journal entry automation
- **Progress Tracking**: Real-time tracking of purchase and delivery progress
- **Document Linking**: Automatic linking of related documents (Invoices, Orders, Receipts)

---

## Installation

### Prerequisites
- Frappe Framework installed
- ERPNext installed
- Python 3.10+
- MySQL/MariaDB database

### Installation Steps

1. **Get the app**:
```bash
cd /path/to/your/frappe-bench
bench get-app fateh_logistics
```

2. **Install on your site**:
```bash
bench --site your-site-name install-app fateh_logistics
```

3. **Run migration**:
```bash
bench --site your-site-name migrate
```

4. **Restart bench**:
```bash
bench restart
```

### Post-Installation Setup

1. **Configure Custom Fields**: The app automatically creates custom fields on standard ERPNext doctypes:
   - Purchase Order, Purchase Invoice, Purchase Receipt
   - Sales Order, Sales Invoice, Delivery Note
   - Journal Entry, Stock Entry
   - Delivery Trip

2. **Set Up Roles**: The app includes the following roles:
   - Operations Executive
   - Warehouse Executive

3. **Verify Fixtures**: Ensure all fixtures are synced:
   - Custom Fields
   - Client Scripts
   - Server Scripts
   - Property Setters
   - Workflows

---

## Core Concepts

### Job Record
The **Job Record** is the central document in Fateh Logistics. It represents a single logistics job that can span multiple operations and documents.

**Key Characteristics**:
- Links to customer quotations
- Tracks items and quantities
- Monitors purchase and delivery progress
- Links to all related vouchers (Invoices, Orders, Receipts)
- Tracks expenses and calculates total costs
- Supports multiple job types

### Job Types
The system supports the following job types:
- **Land Transport**: Road transportation services
- **Warehouse**: Warehouse storage and management
- **Packing**: Packing services
- **Crating**: Crating services
- **Customs Clearance**: Customs clearance operations
- **Terminal Handling**: Terminal handling services

### Job Status
Jobs progress through the following statuses:
- **Pending**: Job created but not started
- **In Progress**: Job is actively being processed
- **Completed**: Job is fully completed
- **On Hold**: Job temporarily paused
- **Cancelled**: Job cancelled

### Progress Tracking
The system automatically tracks:
- **Percent Purchased**: Based on Purchase Orders, Purchase Invoices, and Purchase Receipts
- **Percent Delivered**: Based on Sales Orders, Sales Invoices, and Delivery Notes

---

## Key Doctypes

### 1. Job Record
**Purpose**: Central document for tracking logistics jobs

**Key Fields**:
- `naming_series`: Auto-generated job number
- `date`: Job creation date
- `company`: Company handling the job
- `customer`: Customer for the job
- `job_type`: Type of logistics service
- `job_status`: Current status
- `custom_quotation`: Linked quotation
- `total_expense`: Calculated total expenses
- `items`: Child table with items/quantities
- `custom_vouchers2`: Related vouchers table

**Features**:
- Auto-fetch items from quotations
- Track purchase and delivery progress
- Link to all related documents
- Calculate total expenses
- Support for multiple job types

### 2. Warehouse Job Record
**Purpose**: Specialized job record for warehouse operations

**Key Features**:
- Links to standard ERPNext documents
- Tracks warehouse-specific operations
- Custom fields for warehouse management

### 3. Expense Request
**Purpose**: Track and approve expenses related to jobs

**Key Features**:
- Expense item details
- Approval workflow
- Automatic Journal Entry creation
- Links to Job Records
- Project and Cost Center tracking

### 4. Survey Report
**Purpose**: Document survey details for logistics jobs

**Key Features**:
- Links to Job Records
- Survey details and findings
- Custom print formats

### 5. Packing List
**Purpose**: Track packing details for shipments

**Key Features**:
- Links to Job Records
- Packing item details
- Quantity and weight tracking

### 6. Truck Way Bill
**Purpose**: Manage truck waybill documents

**Key Features**:
- Links to Job Records via `reference_job_record`
- Transportation details
- Vehicle information

### 7. Related Voucher
**Purpose**: Child table in Job Record to track related documents

**Fields**:
- `reference_doctype`: Type of document (Sales Invoice, Purchase Order, etc.)
- `reference_record`: Name of the document
- `amount`: Amount from the document

### 8. Job Item Detail
**Purpose**: Child table in Job Record for items

**Fields**:
- `item`: Item code
- `item_name`: Item name
- `quantity`: Quantity
- `uom`: Unit of Measure
- `rate`: Rate per unit
- `amount`: Total amount
- `from_quotation`: Source quotation

### 9. Job Expense Detail
**Purpose**: Child table for tracking expenses

**Fields**:
- Expense details
- Amount
- Description

### 10. Vehicle Details
**Purpose**: Track vehicle information for transportation jobs

### 11. Operational Status
**Purpose**: Track operational status updates

### 12. Package Details
**Purpose**: Track package information

### 13. Vendor Details
**Purpose**: Track vendor information

### 14. Storage Information
**Purpose**: Track storage details for warehouse jobs

### 15. Stock Movement Detail
**Purpose**: Track stock movements

---

## Workflows

### Job Record Workflow

1. **Create Job Record**
   - Select customer
   - Choose job type
   - Optionally link to quotation
   - Add items manually or fetch from quotations

2. **Add Items**
   - Manual entry
   - Fetch from linked quotation
   - Fetch from multiple quotations

3. **Create Related Documents**
   - Purchase Orders (for purchasing items)
   - Sales Orders (for selling items)
   - Purchase Invoices
   - Sales Invoices
   - Delivery Notes
   - Purchase Receipts
   - Stock Entries

4. **Track Progress**
   - System automatically calculates:
     - Percent Purchased
     - Percent Delivered

5. **Track Expenses**
   - Create Expense Requests
   - Link to Job Record
   - System calculates total expenses

6. **Complete Job**
   - Update job status to "Completed"
   - Review all linked documents
   - Review financial summary

### Expense Request Workflow

1. **Create Expense Request**
   - Link to Job Record (optional)
   - Add expense items
   - Set project and cost center

2. **Submit for Approval**
   - Workflow: Pending Approval → Approved

3. **Automatic Journal Entry**
   - When approved, system creates Journal Entry
   - Debits expense accounts
   - Credits payment account

4. **Track in Job Record**
   - Expenses automatically reflected in Job Record's total expense

### Document Linking Workflow

When creating standard ERPNext documents (Purchase Order, Sales Invoice, etc.):

1. **Link to Job Record**
   - Select Job Record in custom field
   - System validates link

2. **Auto-populate Items**
   - For Purchase Orders: Get remaining items from Job Record
   - Prevents duplicate ordering

3. **Progress Update**
   - On submit/cancel/amend, system updates Job Record progress percentages

---

## APIs

### 1. `get_remaining_items_from_job(job_record_id, target_doctype)`
**Purpose**: Get items from Job Record that haven't been fully ordered yet

**Parameters**:
- `job_record_id`: Name of the Job Record
- `target_doctype`: One of: 'Purchase Order', 'Purchase Invoice', 'Sales Order', 'Sales Invoice', 'Quotation'

**Returns**: Array of items with remaining quantities

**Usage Example**:
```javascript
frappe.call({
    method: 'fateh_logistics.api.get_remaining_items_from_job',
    args: {
        job_record_id: 'JOB-00001',
        target_doctype: 'Purchase Order'
    },
    callback: function(r) {
        // r.message contains array of items
    }
});
```

### 2. `get_quotations_for_customer(customer)`
**Purpose**: Get all submitted quotations for a customer

**Parameters**:
- `customer`: Customer name

**Returns**: Array of quotations

**Usage Example**:
```javascript
frappe.call({
    method: 'fateh_logistics.api.get_quotations_for_customer',
    args: {
        customer: 'Customer ABC'
    },
    callback: function(r) {
        // r.message contains quotations
    }
});
```

### 3. `get_items_from_multiple_quotations(quotations)`
**Purpose**: Get consolidated items from multiple quotations

**Parameters**:
- `quotations`: Array of quotation names

**Returns**: Object with consolidated items

**Usage Example**:
```javascript
frappe.call({
    method: 'fateh_logistics.api.get_items_from_multiple_quotations',
    args: {
        quotations: ['QTN-00001', 'QTN-00002']
    },
    callback: function(r) {
        // r.message.items contains consolidated items
    }
});
```

### 4. `update_percent_purchased(job_record)`
**Purpose**: Update the percent purchased for a Job Record

**Parameters**:
- `job_record`: Job Record name

**Returns**: Updated percentage

**Note**: Called automatically on Purchase Order/Invoice/Receipt submit/cancel/amend

### 5. `update_percent_delivered(job_record)`
**Purpose**: Update the percent delivered for a Job Record

**Parameters**:
- `job_record`: Job Record name

**Returns**: Updated percentage

**Note**: Called automatically on Sales Order/Invoice/Delivery Note submit/cancel/amend

### 6. `get_expense_entries_for_job(job_record_id)`
**Purpose**: Get all approved expense entries for a Job Record

**Parameters**:
- `job_record_id`: Job Record name

**Returns**: Array of expense entry references

---

## Features

### 1. Automatic Item Fetching
- Fetch items from linked quotation
- Fetch items from multiple quotations
- Consolidate quantities from multiple sources
- Prevent duplicate entries

### 2. Progress Tracking
- **Percent Purchased**: Automatically calculated based on:
  - Purchase Orders
  - Purchase Invoices
  - Purchase Receipts
- **Percent Delivered**: Automatically calculated based on:
  - Sales Orders
  - Sales Invoices
  - Delivery Notes

### 3. Document Linking
All standard ERPNext documents can be linked to Job Records:
- Purchase Order → `custom_job_record`
- Purchase Invoice → `custom_job_record`
- Purchase Receipt → `custom_job_record`
- Sales Order → `custom_job_record`
- Sales Invoice → `custom_job_record`
- Delivery Note → `custom_job_record`
- Journal Entry → `custom_job_record`
- Stock Entry → `custom_job_record`
- Delivery Trip → `custom_select_job`

### 4. Expense Management
- Create expense requests linked to jobs
- Approval workflow
- Automatic Journal Entry creation
- Track total expenses per job
- Project and Cost Center integration

### 5. Custom Print Formats
- Quotation2: Custom quotation format
- Survey Report: Survey report format
- Truck Way Bill: Waybill format
- RV Print: Receipt format
- Stock Movement Details: Stock movement format

### 6. Client Scripts
Enhanced user experience with client-side scripts:
- Purchase Order: Auto-fetch remaining items
- Sales Order: Job Record integration
- Quotation: Job Record linking
- Job Record: Multiple quotation selection, expense tracking

### 7. Server Scripts
Automated server-side processing:
- Job Record: Automatic calculations and validations

### 8. Property Setters
Custom field behaviors:
- Hidden fields
- Default values
- Field ordering
- Print visibility

---

## Customizations

### Custom Fields Added

#### Standard Doctypes
1. **Purchase Order**
   - `custom_job_record`: Link to Job Record

2. **Purchase Invoice**
   - `custom_job_record`: Link to Job Record
   - `custom_warehouse_job_record`: Link to Warehouse Job Record

3. **Purchase Receipt**
   - `custom_job_record`: Link to Job Record
   - `custom_warehouse_job_record`: Link to Warehouse Job Record

4. **Sales Order**
   - `custom_job_record`: Link to Job Record

5. **Sales Invoice**
   - `custom_job_record`: Link to Job Record
   - `custom_warehouse_job_record`: Link to Warehouse Job Record

6. **Delivery Note**
   - `custom_job_record`: Link to Job Record
   - `custom_warehouse_job_record`: Link to Warehouse Job Record

7. **Journal Entry**
   - `custom_job_record`: Link to Job Record
   - `custom_warehouse_job_record`: Link to Warehouse Job Record

8. **Stock Entry**
   - `custom_job_record`: Link to Job Record

9. **Delivery Trip**
   - `custom_select_job`: Link to Job Record
   - `custom_warehouse_job_record`: Link to Warehouse Job Record

10. **Customer**
    - `custom_sales_person`: Link to Sales Person

11. **Quotation**
    - `custom_survey_report`: Link to Survey Report
    - Multiple other custom fields for logistics details

### Document Events (Hooks)

The app hooks into standard ERPNext document events:

1. **Purchase Order**
   - `on_submit`: Update Job Record percent purchased
   - `on_cancel`: Update Job Record percent purchased
   - `on_amend`: Update Job Record percent purchased

2. **Purchase Invoice**
   - `on_submit`: Update Job Record percent purchased
   - `on_cancel`: Update Job Record percent purchased
   - `on_amend`: Update Job Record percent purchased

3. **Purchase Receipt**
   - `on_submit`: Update Job Record percent purchased
   - `on_cancel`: Update Job Record percent purchased
   - `on_amend`: Update Job Record percent purchased

4. **Sales Order**
   - `on_submit`: Update Job Record percent delivered
   - `on_cancel`: Update Job Record percent delivered
   - `on_amend`: Update Job Record percent delivered

5. **Sales Invoice**
   - `on_submit`: Update Job Record percent delivered
   - `on_cancel`: Update Job Record percent delivered
   - `on_amend`: Update Job Record percent delivered

6. **Delivery Note**
   - `on_submit`: Update Job Record percent delivered
   - `on_cancel`: Update Job Record percent delivered
   - `on_amend`: Update Job Record percent delivered

7. **Expense Request**
   - `on_update`: Calculate totals, create Journal Entry if approved

---

## Reports

The app includes several built-in reports:

1. **Job Record Report**: Basic job record listing
2. **Job Details Report**: Detailed job information
3. **Job Record Report Detailed**: Comprehensive job details
4. **Job Records**: Job record summary
5. **Job Record Financial Summary**: Financial overview of jobs
6. **Warehouse Job Record Report**: Warehouse-specific job reports

### Accessing Reports
Navigate to: **Logistics > Reports > [Report Name]**

---

## Usage Examples

### Example 1: Creating a Job Record from Quotation

1. **Create Quotation**
   - Go to Selling > Quotation
   - Create quotation with items
   - Submit quotation

2. **Create Job Record**
   - Go to Logistics > Job Record > New
   - Select customer
   - Click "Get Items from Quotation"
   - Select quotation(s)
   - Items are auto-populated
   - Save and submit

3. **Create Purchase Order**
   - Go to Buying > Purchase Order > New
   - Select Job Record in custom field
   - Items are auto-populated from Job Record
   - Complete and submit

### Example 2: Tracking Job Progress

1. **View Job Record**
   - Open Job Record
   - Check "Percent Purchased" and "Percent Delivered" fields
   - These update automatically as related documents are submitted

2. **View Related Documents**
   - Scroll to "Vouchers" tab
   - Click "Fetch Vouchers" button
   - System fetches all linked documents
   - View amounts and status

### Example 3: Expense Management

1. **Create Expense Request**
   - Go to Logistics > Expense Request > New
   - Link to Job Record (optional)
   - Add expense items
   - Set project and cost center
   - Submit for approval

2. **Approve Expense**
   - Approver reviews and approves
   - System automatically creates Journal Entry
   - Expense is reflected in Job Record's total expense

### Example 4: Multiple Quotation Selection

1. **Create Job Record**
   - Select customer
   - Click "Get Items from Quotation"
   - System shows all submitted quotations for customer
   - Select multiple quotations using checkboxes
   - Click "Get Items"
   - Items from all selected quotations are consolidated

### Example 5: Warehouse Job

1. **Create Warehouse Job Record**
   - Go to Logistics > Warehouse Job Record > New
   - Fill in warehouse-specific details
   - Link to related documents
   - Track warehouse operations

---

## Troubleshooting

### Common Issues

#### 1. Custom Fields Not Appearing
**Problem**: Custom fields not showing on standard doctypes

**Solution**:
```bash
bench --site your-site-name migrate
bench --site your-site-name clear-cache
```

#### 2. Progress Percentages Not Updating
**Problem**: Percent purchased/delivered not updating

**Solution**:
- Ensure related documents are submitted (not just saved)
- Check that documents have `custom_job_record` field populated
- Verify document events are firing (check server logs)

#### 3. Items Not Fetching from Job Record
**Problem**: Purchase Order not auto-populating items

**Solution**:
- Ensure Job Record has items in the items table
- Check that Job Record is linked in Purchase Order
- Verify client script is loaded (check browser console)

#### 4. Journal Entry Not Created
**Problem**: Expense Request approved but no Journal Entry

**Solution**:
- Check Expense Request status is "Approved"
- Verify Mode of Payment has linked account
- Check server logs for errors
- Ensure workflow is properly configured

#### 5. Duplicate Property Setter Error
**Problem**: Error during migration about duplicate property setter

**Solution**:
- Check `fixtures/property_setter.json` for duplicates
- Remove duplicate entries
- Re-run migration

#### 6. Missing Custom Field Error
**Problem**: Error about unknown column in database

**Solution**:
- Ensure custom field exists in `fixtures/custom_field.json`
- Run migration to create missing fields
- Check that field is in correct doctype

### Debugging Tips

1. **Check Server Logs**:
```bash
bench --site your-site-name logs
```

2. **Check Browser Console**: For client-side script errors

3. **Verify Fixtures**:
```bash
bench --site your-site-name console
```
Then in console:
```python
import frappe
frappe.get_all('Custom Field', filters={'module': 'Fateh Logistics'})
```

4. **Clear Cache**:
```bash
bench --site your-site-name clear-cache
bench restart
```

---

## Best Practices

1. **Always Link Documents**: When creating Purchase Orders, Sales Invoices, etc., always link to Job Record for proper tracking

2. **Use Quotations**: Create quotations first, then create Job Records from them for better data consistency

3. **Track Expenses**: Use Expense Requests for all job-related expenses to maintain accurate cost tracking

4. **Update Status**: Regularly update Job Record status to reflect current state

5. **Review Reports**: Use built-in reports to monitor job progress and financials

6. **Backup Data**: Regular backups before major operations

---

## Support and Contribution

### Getting Help
- Check this documentation first
- Review server and browser logs
- Contact: ramees@enfono.com

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Code Standards
- Follow Frappe coding standards
- Use pre-commit hooks
- Write tests for new features
- Update documentation

---

## Version History

### Current Version
- Full logistics module functionality
- Integration with ERPNext
- Expense management
- Progress tracking
- Multiple job types support

---

## License

MIT License - See LICENSE file for details

---

**Last Updated**: 2025-01-22
**App Version**: 1.0.0
**Compatible with**: Frappe Framework v15+, ERPNext v15+


