import frappe

@frappe.whitelist()
def get_supplier_summary(references):
	import json
	references = json.loads(references)
	summary = {}

	for reference in references:
		if reference["supplier"] in summary:
			summary[reference["supplier"]] += reference["amount"]
		else:
			summary[reference["supplier"]] = reference["amount"]
	result = []
	for k, v in summary.items():
		data = {
			"supplier": k,
			"amount": v
		}
		result.append(data)
	return result

def validate_summary(self, method):
	if len(self.summary) <= 0:
		frappe.throw("Please validate the summary")
	
	default_mode_of_transfer = frappe.get_doc("Mode of Transfer", self.default_mode_of_transfer)

	for payment in self.summary:
		if payment.mode_of_transfer:
			mode_of_transfer = frappe.get_doc("Mode of Transfer", payment.mode_of_transfer)
		else:
			mode_of_transfer = default_mode_of_transfer
			payment.mode_of_transfer = default_mode_of_transfer.mode

		if payment.amount < mode_of_transfer.minimum_limit or payment.amount > mode_of_transfer.maximum_limit:
			frappe.throw(f"Mode of Transfer not suitable for {payment.supplier} for {payment.amount}. {mode_of_transfer.mode}: {mode_of_transfer.minimum_limit}-{mode_of_transfer.maximum_limit}")