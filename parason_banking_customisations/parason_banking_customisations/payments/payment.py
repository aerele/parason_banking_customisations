import frappe
import requests
import json
import hashlib
from Crypto.Cipher import AES
from base64 import b64decode, b64encode
from Crypto.Util.Padding import unpad
from datetime import datetime
from frappe.utils import flt, getdate, nowdate, today


@frappe.whitelist()
def process_payment(payment_info):
	if not payment_info:
		return
	data = make_request_payload(payment_info)
	checksum = calculate_checsum(data=data["TransferPaymentRequest"]["TransferPaymentRequestBody"])
	data["TransferPaymentRequest"]["TransferPaymentRequestBody"]["checksum"] = checksum

	aes_key = "98055A8E48EC727B8B3946F312E4D89F"
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


	url = "https://sakshamuat.axisbank.co.in/gateway/api/txb/v1/payments/transfer-payment"
	headers = {
			'Content-Type': 'application/json',
			'X-IBM-Client-Id': '070fa58a-c541-429e-9332-583be8da305d',
			'X-IBM-Client-Secret': 'L8rX7rE1iW0vR5kF8gU5iI5wR3cR1sW0hQ5wO2yO3aI2sR1lK5',
			'Accept': 'application/json'
	}

	response = requests.request("POST", url, headers=headers, data=json.dumps(payload), cert=("/home/frappeuser/sixa_test/client_cert.txt", "/home/frappeuser/sixa_test/parason_plain.key"))

	
def make_request_payload(payment_info):
	paymode = frappe.db.get_value("Bank Integration Mode", payment_info.mode_of_transfer, "short_code")
	bank_account = frappe.get_doc("Bank Account", payment_info.bank_account)
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
					"corpAccNum": "248012910169",
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

def unpad(byte_array:bytearray):
	return byte_array[:-ord(byte_array[-1:])]

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
	cipher= AES.new(key, AES.MODE_CBC, IV)
	# decrypt and decode
	decrypted = cipher.decrypt(message)
	# unpad - with pkcs5 style and return 
	return unpad(decrypted)