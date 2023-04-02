import frappe
from frappe.utils import nowdate
import json
import uuid


@frappe.whitelist()
def get_supplier_summary(references, company_bank_account):
	import json
	references = json.loads(references)
	if not len(references) or not company_bank_account:
		return
	supplier_bank_account, supplier_account = validate_supplier_bank_accounts(references)
	summary = {}

	for reference in references:
		summary_key = reference["supplier"] + "{}" +  reference["plant"]
		if summary_key  in summary:
			summary[summary_key] += reference["amount"]
		else:
			summary[summary_key] = reference["amount"]
	result = []
	for k, v in summary.items():
		sum_plant = k.split("{}")
		data = {
			"supplier": sum_plant[0],
			"plant": sum_plant[1],
			"amount": v
		}
		result.append(data)
	
	for row in result:
		row["bank_account"] = supplier_bank_account[row["supplier"]]
		row["account"] = supplier_account[row["supplier"]]

		supplier_bank = frappe.db.get_value("Bank Account", row["bank_account"], "bank")
		company_bank = frappe.db.get_value("Bank Account", company_bank_account, "bank")
		row["mode_of_transfer"] = None
		if supplier_bank == company_bank:
			mode_of_transfer = frappe.db.get_value("Mode of Transfer", {"is_bank_specific": 1, "bank": supplier_bank})
			if mode_of_transfer:
				row["mode_of_transfer"] = mode_of_transfer
		else:
			mot = frappe.db.get_value("Mode of Transfer", {
				"minimum_limit": ["<=", row["amount"]], 
				"maximum_limit": [">", row["amount"]],
				"is_bank_specific": 0
				}, 
				order_by = "priority asc")
			if mot:
				row["mode_of_transfer"] = mot


	return result

def validate(self, method):
	validate_summary(self, method)

def validate_supplier_bank_accounts(references):
	supplier_bank_account = {}
	for row in references:
		row = frappe._dict(row)
		if not row.supplier in supplier_bank_account:
			supplier_bank_account[row.supplier] = row.bank_account
			continue
		if supplier_bank_account[row.supplier] != row.bank_account:
			frappe.throw(f"{row.supplier} is having two bank accounts - {supplier_bank_account[row.supplier]}, {row.bank_account}. Make another payment order for one of them")

	supplier_account = {}
	for row in references:
		row = frappe._dict(row)
		if not row.type or (row.type and row.type == "Purchase Order"):
			if not row.account in supplier_account:
				supplier_account[row.supplier] = row.account
				continue
			if supplier_account[row.supplier] != row.account:
				frappe.throw(f"{row.supplier} is having two accounts to reconcile - {supplier_account[row.supplier]}, {row.account}. Make another payment order for one of them")

	return supplier_bank_account, supplier_account


def validate_summary(self, method):
	if len(self.summary) <= 0:
		frappe.throw("Please validate the summary")
	
	default_mode_of_transfer = None
	if self.default_mode_of_transfer:
		default_mode_of_transfer = frappe.get_doc("Mode of Transfer", self.default_mode_of_transfer)

	for payment in self.summary:
		if payment.mode_of_transfer:
			mode_of_transfer = frappe.get_doc("Mode of Transfer", payment.mode_of_transfer)
		else:
			if not default_mode_of_transfer:
				frappe.throw("Define a specific mode of transfer or a default one")
			mode_of_transfer = default_mode_of_transfer
			payment.mode_of_transfer = default_mode_of_transfer.mode

		if payment.amount < mode_of_transfer.minimum_limit or payment.amount > mode_of_transfer.maximum_limit:
			frappe.throw(f"Mode of Transfer not suitable for {payment.supplier} for {payment.amount}. {mode_of_transfer.mode}: {mode_of_transfer.minimum_limit}-{mode_of_transfer.maximum_limit}")

	summary_total = 0
	references_total = 0
	for ref in self.references:
		references_total += ref.amount
	
	for sum in self.summary:
		summary_total += sum.amount

	if summary_total != references_total:
		frappe.throw("Summary isn't matching the references")


@frappe.whitelist()
def make_bank_payment(docname):
	roles = frappe.get_roles(frappe.session.user)
	if not "Bank Payment Approver - 02" in roles:
		frappe.throw("No Permission to initiate")

	payment_order_doc = frappe.get_doc("Payment Order", docname)
	on_hold_count = 0
	approved_count = 0
	for i in payment_order_doc.summary:
		if i.payment_initiated:
			continue

		if i.approval_status in ["Put to Hold", "Rejected"]:
			continue

		if i.approval_status == "Put to Hold":
			on_hold_count += 1
		elif i.approval_status == "Approved":
			approved_count += 1
			frappe.db.set_value("Payment Order Summary", i.name, "payment_initiated", 1)

	if on_hold_count:
		frappe.db.set_value("Payment Order", docname, "status", "Partially Initiated")
	elif approved_count:
		frappe.db.set_value("Payment Order", docname, "status", "Initiated")

	# Commenting the payments as it returns: "message":"Open API Access not allowed","status":"F"
	#validate_payment(docname)
	#process_payment(docname)
	#status = update_payment_status(docname)

	return {"message": f"{approved_count} payments initiated"}

@frappe.whitelist()
def modify_approval_status(items, approval_status):
	if not items:
		return
	
	if isinstance(items, str):
		items = json.loads(items)
	line_item_status = {}
	for item in items:
		line_item_status[item] = {"status": None, "message": ""}
		pos_doc = frappe.get_doc("Payment Order Summary", item)
		if pos_doc.payment_initiated:
			line_item_status[item] = {"status": 0, "message": f"Payment already initiated for {pos_doc.supplier} - {pos_doc.amount}"}
			continue
		if pos_doc.payment_rejected:
			line_item_status[item] = {"status": 0, "message": f"Payment already rejected for {pos_doc.supplier} - {pos_doc.amount}"}
			continue
		frappe.db.set_value("Payment Order Summary", item, "approval_status", approval_status)
		line_item_status[item] = {
			"status": 1, 
			"message": approval_status
		}

	return line_item_status


@frappe.whitelist()
def make_payment_entries(docname):
	payment_order_doc = frappe.get_doc("Payment Order", docname)
	"""create entry"""
	frappe.flags.ignore_account_permission = True

	# if not doc.is_ad_hoc:
	# 	ref_doc = frappe.get_doc(doc.reference_doctype, doc.reference_name)
	# party_account = frappe.db.get_value("Payment Request Type", doc.payment_type, "account_paid_to")
	is_advance_payment = "Yes"
	is_adhoc = 0
	for ref in payment_order_doc.references:
		if ref.reference_doctype == "Purchase Invoice":
			is_advance_payment = "No"
		if ref.is_adhoc:
			is_adhoc = 1
		


	for row in payment_order_doc.summary:
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Pay"
		pe.payment_entry_type = "Pay"
		pe.company = payment_order_doc.company
		pe.plant = row.plant
		pe.posting_date = nowdate()
		pe.mode_of_payment = "Wire Transfer"
		pe.party_type = "Supplier"
		pe.party = row.supplier
		pe.is_advance_payment = is_advance_payment
		pe.bank_account = payment_order_doc.company_bank_account
		pe.party_bank_account = row.bank_account
		pe.ensure_supplier_is_not_blocked()
		pe.payment_order = payment_order_doc.name

		pe.paid_from = payment_order_doc.account
		if row.account:
			pe.paid_to = row.account
		pe.paid_from_account_currency = "INR"
		pe.paid_to_account_currency = "INR"
		pe.paid_amount = row.amount
		pe.received_amount = row.amount
		pe.letter_head = frappe.db.get_value("Letter Head", {"is_default": 1}, "name")


		if not is_adhoc:
			for reference in payment_order_doc.references:
				if reference.supplier == row.supplier and reference.plant == row.plant:
					pe.append(
						"references",
						{
							"reference_doctype": reference.reference_doctype,
							"reference_name": reference.reference_name,
							"total_amount": reference.amount,
							"allocated_amount": reference.amount,
						},
					)
		pe.update(
			{
				"reference_no": payment_order_doc.name,
				"reference_date": nowdate(),
				"remarks": "Payment Entry from Payment Order - {0}".format(
					payment_order_doc.name
				),
			}
		)

		pe.setup_party_account_field()
		pe.set_missing_values()
		pe.insert(ignore_permissions=True)
		pe.submit()
		frappe.db.set_value("Payment Order Summary", row.name, "payment_entry", pe.name)


@frappe.whitelist()
def log_payload(docname):
	payment_order_doc = frappe.get_doc("Payment Order", docname)
	for row in payment_order_doc.summary:
		short_code = frappe.db.get_value("Bank Integration Mode", {"parent": payment_order_doc.company_bank_account, "mode_of_transfer": row.mode_of_transfer}, "short_code")
		bank_account = frappe.get_doc("Bank Account", row.bank_account)
		brl = frappe.new_doc("Bank API Request Log")
		brl.payment_order = payment_order_doc.name
		brl.payload = json.dumps(str({
			"TransferPaymentRequest": {
				"SubHeader": {
					"requestUUID": str(uuid.uuid4()),
					"serviceRequestId": "OpenAPI",
					"serviceRequestVersion": "1.0",
					"channelId": "PARASON"
				},
				"TransferPaymentRequestBody": {
					"channelId": "PARASON",
					"corpCode": "Parason",
					"paymentDetails": [
						{
							"txnPaymode": short_code,
							"custUniqRef": row.name,
							"corpAccNum": "248012910169",
							"valueDate": str(payment_order_doc.posting_date),
							"txnAmount": row.amount,
							"beneName": bank_account.account_name,
							"beneCode": bank_account.name,
							"beneAccNum": bank_account.bank_account_no,
							"beneAcType": "11",
							"beneIfscCode": bank_account.branch_code,
							"beneBankName": bank_account.bank
						}
					]
				}
			}
		}))
		brl.status = "Initiated"
		brl.save()
		brl.submit()

