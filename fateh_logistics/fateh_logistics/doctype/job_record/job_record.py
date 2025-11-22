# Copyright (c) 2025, siva@enfono.in and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class JobRecord(Document):
	def validate(self):
		total_value = 0
		item_profit = 0
		if not hasattr(self, 'items') or not self.items:
			return
		for row in self.items:
			if not row.item:
				continue

			if self.get_valuation_rate_from == "Latest Purchase":
				row.valuation_rate = get_latest_purchase_rate(row.item)
				row.valuation_amount = row.quantity * row.valuation_rate
				row.profit = row.amount - row.valuation_amount

			elif self.get_valuation_rate_from == "Stock Ledger":
				row.valuation_rate = get_stock_valuation_rate(row.item)
				row.valuation_amount = row.quantity * row.valuation_rate
				row.profit = row.amount - row.valuation_amount

			else:
				row.valuation_rate = 0.0
				row.valuation_amount = row.quantity * row.valuation_rate
				row.profit = row.amount - row.valuation_amount
				
			total_value += row.valuation_amount
			item_profit += row.profit
		self.total_valuation = total_value
		self.item_profit = item_profit


def get_latest_purchase_rate(item_code):
    result = frappe.db.sql("""
        SELECT pi_item.rate
        FROM `tabPurchase Invoice Item` pi_item
        JOIN `tabPurchase Invoice` pi ON pi.name = pi_item.parent
        WHERE pi_item.item_code = %s AND pi.docstatus = 1
        ORDER BY pi.posting_date DESC, pi.creation DESC
        LIMIT 1
    """, (item_code,), as_dict=1)
    return result[0].rate if result else 0.0


def get_stock_valuation_rate(item_code):
    result = frappe.db.sql("""
        SELECT valuation_rate
        FROM `tabStock Ledger Entry`
        WHERE item_code = %s AND valuation_rate IS NOT NULL
        ORDER BY posting_date DESC, posting_time DESC, creation DESC
        LIMIT 1
    """, (item_code,), as_dict=1)
    return result[0].valuation_rate if result else 0.0
		