import frappe
import requests
import json
import hashlib
from Crypto.Cipher import AES
from base64 import b64decode, b64encode
from Crypto.Util.Padding import unpad
from frappe.utils import today
from frappe.contacts.doctype.address.address import get_default_address



@frappe.whitelist()
def process_payment(payment_info, company_bank_account, invoices = None):
	if not payment_info:
		return False
	
	if not company_bank_account:
		frappe.throw("Company bank account is not available")
		return False

	bank_integration_doc = frappe.get_doc("Bank Integration Settings", company_bank_account)

	if not bank_integration_doc:
		frappe.throw(f"Bank Integrtation Settings is not available for {company_bank_account}")
		return False
	try:
		data = make_request_payload(payment_info, company_bank_account, invoices = invoices)
		checksum = calculate_checsum(data=data["TransferPaymentRequest"]["TransferPaymentRequestBody"])
		data["TransferPaymentRequest"]["TransferPaymentRequestBody"]["checksum"] = checksum

		aes_key = bank_integration_doc.get_password(fieldname="aes_key")
		n = 2
		aes_key_array = [aes_key[i:i+n] for i in range(0, len(aes_key), n)]
		# print(aes_key_array)

		key_byte_list = []
		for i in aes_key_array:
			key_byte_list.append(int(i, 16))

		# print(key_byte_list)
		# print(bytearray(key_byte_list))


		encrypted_data = encrypt_data(data["TransferPaymentRequest"]["TransferPaymentRequestBody"], bytearray(key_byte_list))
		# print(encrypted_data)

		# decrypted_data = decrypt_data(encrypted_data, aes_key) 
		# print(decrypted_data)

		payment_request_data = {}
		payment_request_data["SubHeader"] = data["TransferPaymentRequest"]["SubHeader"]
		payment_request_data["TransferPaymentRequestBodyEncrypted"] = encrypted_data
		#payment_request_data["TransferPaymentRequestBody"] = data["TransferPaymentRequest"]["TransferPaymentRequestBody"]

		payload = {}
		payload["TransferPaymentRequest"] = payment_request_data


		url = frappe.db.get_value("Bank Integration Link", {"parent": bank_integration_doc.name, "type": "Payout"}, "url")
		headers = {
			'Content-Type': 'application/json',
			'X-IBM-Client-Id': bank_integration_doc.get_password(fieldname="client_id"),
			'X-IBM-Client-Secret': bank_integration_doc.get_password(fieldname="client_secret"),
			'Accept': 'application/json'
		}

		request_log = frappe.new_doc("Bank API Request Log")
		request_log.payment_order = payment_info.parent
		request_log.payload = json.dumps(data)

		cert_file = frappe.get_doc("File", {"file_url": bank_integration_doc.signing_certificate})
		key_file = frappe.get_doc("File", {"file_url": bank_integration_doc.private_key})
		response = requests.request("POST", url, headers=headers, data=json.dumps(payload), cert=(cert_file.get_full_path(), key_file.get_full_path()))
		response_json = json.loads(response.text)
		decrypted_text = decrypt_data(response_json["TransferPaymentResponse"]["TransferPaymentResponseBodyEncrypted"], bytearray(key_byte_list))
		request_log.response = decrypted_text
		request_log.status = response.status_code
		request_log.insert()

		if response.status_code not in [201, 200]:
			return False
		
		if json.loads(decrypted_text)["status"] == "F":
			return False

		return True
	except:
		return False

def make_request_payload(payment_info, company_bank_account, invoices = None):
	paymode = frappe.db.get_value("Bank Integration Mode", {"mode_of_transfer": payment_info.mode_of_transfer}, "short_code")
	bank_account = frappe.get_doc("Bank Account", payment_info.bank_account)
	debit_account_no = frappe.db.get_value("Bank Account", company_bank_account, "bank_account_no")

	billing_address_name = get_default_address("Supplier", payment_info.supplier)
	if billing_address_name:
		billing_address = frappe.get_doc("Address", billing_address_name)
	address_title, address_line1, address_line2, city, state, pincode, email_id, phone = "", "", "", "", "", "", "", ""
	if billing_address:
		city = billing_address.city
		state = billing_address.state
		if billing_address.pincode:
			pincode = str(billing_address.pincode)
		else:
			pincode = ""
		address_title = billing_address.address_title
		address_line1 = billing_address.address_line1
		address_line2 = billing_address.address_line2
		email_id = billing_address.email_id
		phone = billing_address.phone

	return {
	"TransferPaymentRequest": {
		"SubHeader": {
			"requestUUID": payment_info.name,
			"serviceRequestId": "OpenAPI",
			"serviceRequestVersion": "1.0",
			"channelId": "PARASON"
		},
		"TransferPaymentRequestBody": {
			"channelId": "PARASON",
			"corpCode": "PARASON",
			"paymentDetails": [
				{
					"txnPaymode": paymode,
					"custUniqRef": payment_info.name,
					"corpAccNum": debit_account_no,
					"valueDate": str(today()),
					"txnAmount": str(payment_info.amount),
					"beneName": bank_account.account_name,
					"beneCode": bank_account.party,
					"beneAccNum": bank_account.bank_account_no,
					"beneAcType": "",
					"beneAddr1": address_title,
					"beneAddr2": address_line1,
					"beneAddr3": address_line2,
					"beneCity": city,
					"beneState": state,
					"benePincode": pincode,
					"beneIfscCode": bank_account.branch_code,
					"beneBankName": bank_account.bank,
					"baseCode": "",
					"chequeNumber": "",
					"chequeDate": "",
					"payableLocation": "",
					"printLocation": "",
					"beneEmailAddr1": email_id,
					"beneMobileNo": phone,
					"productCode": "",
					"txnType": "",
					"invoiceDetails": invoices,
					"enrichment1": "",
					"enrichment2": "",
					"enrichment3": "",
					"enrichment4": "",
					"enrichment5": "",
					"senderToReceiverInfo": ""
				}
			]
		}
	}
}

def NestedDictValues(d):
	for v in d.values():
		if isinstance(v, dict):
			yield from NestedDictValues(v)
		elif isinstance(v, list):
			for i in v:
				yield from NestedDictValues(i)
		else:
			yield v

def calculate_checsum(data):
	all_values = list(NestedDictValues(data))
	final_string = ''
	for s in all_values:
		if s:
			final_string = final_string + s
	return hashlib.md5(final_string.encode('utf-8')).hexdigest()

IV = "0000000000000000".encode("utf-8")
BLOCK_SIZE = 16
def pad(byte_array:bytearray):
	pad_len = BLOCK_SIZE - len(byte_array) % BLOCK_SIZE
	return byte_array + (bytes([pad_len]) * pad_len)

def encrypt_data(data, key):
	data = json.dumps(data)
	# convert to bytes
	byte_array = data.encode("utf-8")
	# pad the message - with pkcs5 style
	padded = pad(byte_array)
	# new instance of AES with encoded key
	cipher = AES.new(key, AES.MODE_CBC, key)
	# now encrypt the padded bytes
	encrypted = cipher.encrypt(padded)
	#append with IV
	# print(IV)
	# print(encrypted)
	encrypted_with_iv = key + encrypted
	# base64 encode and convert back to string
	return  b64encode(encrypted_with_iv).decode('utf-8')

def decrypt_data(data, key):
	# print(data)
	# convert the message to bytes
	byte_array = data.encode("utf-8")
	# base64 decode
	message = b64decode(byte_array)
	# AES instance with the - setKey()
	cipher= AES.new(key, AES.MODE_CBC, message[:AES.block_size])
	# decrypt and decode
	decrypted = cipher.decrypt(message[AES.block_size:])
	# unpad - with pkcs5 style and return 
	return unpad(decrypted, AES.block_size).decode("utf-8")

@frappe.whitelist()
def get_payment_status(payment_info, company_bank_account):
	bank_integration_doc = frappe.get_doc("Bank Integration Settings", company_bank_account)
	try:
		data = make_status_payload(payment_info)
		checksum = calculate_checsum(data=data["GetStatusRequest"]["GetStatusRequestBody"])
		data["GetStatusRequest"]["GetStatusRequestBody"]["checksum"] = checksum

		aes_key = bank_integration_doc.get_password(fieldname="aes_key")
		n = 2
		aes_key_array = [aes_key[i:i+n] for i in range(0, len(aes_key), n)]
		

		key_byte_list = []
		for i in aes_key_array:
			key_byte_list.append(int(i, 16))


		encrypted_data = encrypt_data(data["GetStatusRequest"]["GetStatusRequestBody"], bytearray(key_byte_list))


		payment_request_data = {}
		payment_request_data["SubHeader"] = data["GetStatusRequest"]["SubHeader"]
		payment_request_data["GetStatusRequestBodyEncrypted"] = encrypted_data

		payload = {}
		payload["GetStatusRequest"] = payment_request_data


		
		url = frappe.db.get_value("Bank Integration Link", {"parent": bank_integration_doc.name, "type": "Status"}, "url")
		headers = {
			'Content-Type': 'application/json',
			'X-IBM-Client-Id': bank_integration_doc.get_password(fieldname="client_id"),
			'X-IBM-Client-Secret': bank_integration_doc.get_password(fieldname="client_secret"),
			'Accept': 'application/json'
		}


		cert_file = frappe.get_doc("File", {"file_url": bank_integration_doc.signing_certificate})
		key_file = frappe.get_doc("File", {"file_url": bank_integration_doc.private_key})
		response = requests.request("POST", url, headers=headers, data=json.dumps(payload), cert=(cert_file.get_full_path(), key_file.get_full_path()))
		response_json = json.loads(response.text)

		decrypted_text = decrypt_data(response_json["GetStatusResponse"]["GetStatusResponseBodyEncrypted"], bytearray(key_byte_list))
		if response.status_code not in [201, 200]:
			return

		decrypted_dict = json.loads(decrypted_text)
		if decrypted_dict["status"] == "F":
			return
		
		if "data" in decrypted_dict and decrypted_dict["data"]:
			if "CUR_TXN_ENQ" in decrypted_dict["data"] and len(decrypted_dict["data"]["CUR_TXN_ENQ"]) == 1:
				payment_status = decrypted_dict["data"]["CUR_TXN_ENQ"][0]
				if "crn" in payment_status and payment_status["crn"] and payment_status["crn"] == payment_info.name:
					if payment_status["transactionStatus"] == "PROCESSED":
						if payment_status["utrNo"]:
							frappe.db.set_value("Payment Order Summary", payment_info.name, "reference_number", payment_status["utrNo"])
							frappe.db.set_value("Payment Entry", payment_info.payment_entry, "reference_no", payment_status["utrNo"])
							frappe.db.set_value("Payment Order Summary", payment_info.name, "payment_status", "Processed")
					elif payment_status["transactionStatus"] == "REJECTED":
						frappe.db.set_value("Payment Order Summary", payment_info.name, "payment_status", "Rejected")
						payment_entry_doc = frappe.get_doc("Payment Entry", payment_info.payment_entry)
						payment_entry_doc.cancel()
			else:
				frappe.db.set_value("Payment Order Summary", payment_info.name, "payment_status", "Failed")
				payment_entry_doc = frappe.get_doc("Payment Entry", payment_info.payment_entry)
				payment_entry_doc.cancel()
	except:
		return


def make_status_payload(payment_info):
	return {
		"GetStatusRequest": {
			"SubHeader": {
				"requestUUID": payment_info.name,
				"serviceRequestId": "OpenAPI",
				"serviceRequestVersion": "1.0",
				"channelId": "PARASON"
			},
			"GetStatusRequestBody": {
				"channelId": "PARASON",
				"corpCode": "PARASON",
				"crn": payment_info.name,
			}
		}
	}