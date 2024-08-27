# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_url_to_list
import requests
import random
from datetime import datetime
import json

class LMSSettings(Document):
	def validate(self):
		self.validate_google_settings()

	def validate_google_settings(self):
		if self.send_calendar_invite_for_evaluations:
			google_settings = frappe.get_single("Google Settings")

			if not google_settings.enable:
				frappe.throw(
					_("Enable Google API in Google Settings to send calendar invites for evaluations.")
				)

			if not google_settings.client_id or not google_settings.client_secret:
				frappe.throw(
					_(
						"Enter Client Id and Client Secret in Google Settings to send calendar invites for evaluations."
					)
				)

			calendars = frappe.db.count("Google Calendar")
			if not calendars:
				frappe.throw(
					_(
						"Please add <a href='{0}'>{1}</a> for <a href='{2}'>{3}</a> to send calendar invites for evaluations."
					).format(
						get_url_to_list("Google Calendar"),
						frappe.bold("Google Calendar"),
						get_url_to_list("Course Evaluator"),
						frappe.bold("Course Evaluator"),
					)
				)

@whitelist()
def call_payment_api(phone_number, fullname, amount):
    # Get API credentials from LMS settings doctype
    settings = frappe.get_single('LMS Settings')
    api_key = settings.apikey
    merchant_uid = settings.merchantuid
    api_user_id = settings.apiuserid
    pgaccountid = settings.accountid

    # Create data array similar to PHP version
    data_array = {
        "schemaVersion": "1.0",
        "requestId": str(random.randint(10000, 99999)),
        "timestamp": str(int(datetime.now().timestamp())),
        "channelName": "WEB",
        "serviceName": "API_PURCHASE",
        "sessionId": str(random.randint(20, 100)),
        "serviceParams": {
            "merchantUid": merchant_uid,
            "apiUserId": api_user_id,
            "apiKey": api_key,
            "paymentMethod": "MWALLET_ACCOUNT",
            "pgaccountid": pgaccountid,
            "payerInfo": {
                "accountNo": str(phone_number),
                "accountHolder": fullname
            },
            "transactionInfo": {
                "referenceId": 'testing',
                "invoiceId": str(random.randint(100, 1000)),
                "amount": amount,
                "currency": "USD",
                "description": fullname
            }
        }
    }

    # Convert the data to JSON format
    json_data = json.dumps(data_array)

    # Make the API request
    response = requests.post('https://api.waafi.com/asm', data=json_data, headers={'Content-Type': 'application/json'})

    # Process the response
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get('responseMsg') == "RCS_SUCCESS":
            # Handle success
            frappe.msgprint('Payment was successful.')
            return True
        else:
            # Handle other responses
            frappe.msgprint(f"Payment failed: {response_data.get('responseMsg')}")
            return False
    else:
        frappe.msgprint(f"Error in API call: {response.status_code} - {response.text}")
        return False



