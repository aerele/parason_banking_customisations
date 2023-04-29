import frappe
from erpnext.accounts.doctype.payment_order.payment_order import PaymentOrder
from parason_banking_customisations.parason_banking_customisations.doc_events.payment_order import make_payment_entries

class CustomPaymentOrder(PaymentOrder):
	def on_submit(self):
		make_payment_entries(self.name)
		frappe.db.set_value("Payment Order", self.name, "status", "Pending")

		for ref in self.references:
			if hasattr(ref, "payment_request"):
				frappe.db.set_value("Payment Request", ref.payment_request, "status", "Payment Ordered")

	def on_update_after_submit(self):
		frappe.throw("You cannot modify a payment order")
		return


	def before_cancel(self):
		frappe.throw("You cannot cancel a payment order")
		return
	
	def on_trash(self):
		frappe.throw("You cannot delete a payment order")
		return