import frappe
from frappe import _

def valdidate_bank_for_wire_transfer(self, method):
	if self.mode_of_payment == "Wire Transfer" and not self.bank_account:
		frappe.throw(_("Bank Account is missing for Wire Transfer Payments"))
	
	status = frappe.db.get_value("Bank Account", self.bank_account, "workflow_state")
	if self.mode_of_payment == "Wire Transfer" and status != "Approved":
		frappe.throw(_("Cannot proceed with un-approved bank account"))

@frappe.whitelist()
def make_payment_order(source_name, target_doc=None):
	from frappe.model.mapper import get_mapped_doc

	def set_missing_values(source, target):
		target.payment_order_type = "Payment Request"
		account = ""
		#customize code to fetch account from payment request
		if source.custom_account_paid_to:
			account = source.custom_account_paid_to
		else:
			account = frappe.db.get_value("Payment Type", source.payment_type, "account")
		#end

		# if source.payment_type:
		# 	account = frappe.db.get_value("Payment Type", source.payment_type, "account")

		target.append(
			"references",
			{
				"reference_doctype": source.reference_doctype,
				"reference_name": source.reference_name,
				"amount": source.grand_total,
				"supplier": source.party,
				"payment_request": source_name,
				"mode_of_payment": source.mode_of_payment,
				"bank_account": source.bank_account,
				"account": account,
				"is_adhoc": source.is_adhoc,
				"plant": source.plant
			},
		)
		target.status = "Pending"

	doclist = get_mapped_doc(
		"Payment Request",
		source_name,
		{
			"Payment Request": {
				"doctype": "Payment Order",
			}
		},
		target_doc,
		set_missing_values,
	)

	return doclist

