import frappe
import requests
import json
import hashlib
from Crypto.Cipher import AES
from base64 import b64decode, b64encode
from Crypto.Util.Padding import unpad
from frappe.utils import today


@frappe.whitelist()
def process_payment(payment_info, company_bank_account):
	if not payment_info:
		return False
	
	if not company_bank_account:
		frappe.throw("Company bank account is not available")
		return False

	bank_integration_doc = frappe.get_doc("Bank Integration Settings", company_bank_account)

	if not bank_integration_doc:
		frappe.throw(f"Bank Integrtation Settings is not available for {company_bank_account}")
		return False

	data = make_request_payload(payment_info, company_bank_account)
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
	response = requests.request("POST", url, headers=headers, data=json.dumps(payload), cert=(bank_integration_doc.signing_certificate, bank_integration_doc.private_key))
	response_json = json.loads(response.text)
	decrypted_text = decrypt_data(response_json["GetStatusResponse"]["GetStatusResponseBodyEncrypted"], bytearray(key_byte_list))
	request_log.response = decrypted_text
	request_log.status = response.status_code
	request_log.insert()

	if response.status_code not in [201, 200]:
		return False
	else:
		return True

def make_request_payload(payment_info, company_bank_account):
	paymode = frappe.db.get_value("Bank Integration Mode", payment_info.mode_of_transfer, "short_code")
	bank_account = frappe.get_doc("Bank Account", payment_info.bank_account)
	debit_account_no = frappe.db.get_value("Bank Account", company_bank_account, "bank_account_no")
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
			"corpCode": "Parason",
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
					"beneAddr1": "",
					"beneAddr2": "",
					"beneAddr3": "",
					"beneCity": "",
					"beneState": "",
					"benePincode": "",
					"beneIfscCode": bank_account.branch_code,
					"beneBankName": bank_account.bank,
					"baseCode": "",
					"chequeNumber": "",
					"chequeDate": "",
					"payableLocation": "",
					"printLocation": "",
					"beneEmailAddr1": "",
					"beneMobileNo": "",
					"productCode": "",
					"txnType": "",
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