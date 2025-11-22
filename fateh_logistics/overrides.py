import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

class CustomPE(PaymentEntry):
    
    def set_exchange_gain_loss(self):
        return





