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

@frappe.whitelist(allow_guest=True)
def call_payment_api(phone_number, fullname, amount):
    # Get API credentials from LMS settings doctype
    settings = frappe.get_single('LMS Settings')
    api_key = settings.api_key 
    merchant_uid = settings.merchant_uid 
    api_user_id = settings.api_user_id 
    pgaccountid = settings.account_id 

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
    response = requests.post('https://api.waafipay.com/asm', data=json_data, headers={'Content-Type': 'application/json'})

    try:
        response = requests.post('https://api.waafipay.com/asm', data=json_data, headers={'Content-Type': 'application/json'})
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        # Process the response
        response_data = response.json()
        if response_data.get('responseMsg') == "RCS_SUCCESS":
            return {'status': 'success', 'message': 'Payment was successful.'}
        else:
            return {'status': 'failed', 'message': f"Payment failed: {response_data.get('responseMsg')}"}

    except requests.exceptions.RequestException as e:
        frappe.log_error(frappe.get_traceback(), _("Payment API Error"))
        return {'status': 'error', 'message': f"Error in API call: {str(e)}"}



