import frappe
from erpnext.accounts.doctype.payment_order.payment_order import PaymentOrder

class CustomPaymentOrder(PaymentOrder):
	def on_submit(self):
		pass
