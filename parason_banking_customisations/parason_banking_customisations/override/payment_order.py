import frappe
from erpnext.accounts.doctype.payment_order.payment_order import PaymentOrder
from parason_banking_customisations.parason_banking_customisations.doc_events.payment_order import make_payment_entries

class CustomPaymentOrder(PaymentOrder):
	def on_submit(self):
		make_payment_entries(self.name)

	def on_update_after_submit(self):
		for row in self.summary:
			if row.initial_rejection or row.final_rejection:
				pe_doc = frappe.get_doc("Payment Entry", row.payment_entry)
				if pe_doc.docstatus == 1:
					pe_doc.cancel()

	def on_cancel(self):
		pass