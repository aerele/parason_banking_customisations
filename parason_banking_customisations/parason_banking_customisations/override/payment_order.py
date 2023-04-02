import frappe
from erpnext.accounts.doctype.payment_order.payment_order import PaymentOrder
from parason_banking_customisations.parason_banking_customisations.doc_events.payment_order import make_payment_entries

class CustomPaymentOrder(PaymentOrder):
	def on_submit(self):
		make_payment_entries(self.name)
		frappe.db.set_value("Payment Order", self.name, "status", "Pending Approval")

		for ref in self.references:
			if hasattr(ref, "payment_request"):
				frappe.db.set_value("Payment Request", ref.payment_request, "status", "Payment Ordered")

	def on_update_after_submit(self):
		hold_count = 0
		rejected_acount = 0
		for row in self.summary:
			if row.approval_status == "Rejected":
				rejected_acount += 1
				pe_doc = frappe.get_doc("Payment Entry", row.payment_entry)
				if pe_doc.docstatus == 1:
					pe_doc.cancel()
				frappe.db.set_value("Payment Order Summary", row.name, "payment_status", "Rejected")
				frappe.db.set_value("Payment Order Summary", row.name, "payment_rejected", 1)
			elif row.approval_status == "Put to Hold":
				hold_count += 1
				frappe.db.set_value("Payment Order Summary", row.name, "payment_status", "On Hold")
		if rejected_acount == len(self.summary):
			frappe.db.set_value("Payment Order", self.name, "status", "Rejected")
		elif hold_count:
			frappe.db.set_value("Payment Order", self.name, "status", "Partially Approved")
		else:
			frappe.db.set_value("Payment Order", self.name, "status", "Approved")


	def before_cancel(self):
		frappe.throw("You cannot cancel a payment order")
		return
	
	def on_trash(self):
		frappe.throw("You cannot delete a payment order")
		return