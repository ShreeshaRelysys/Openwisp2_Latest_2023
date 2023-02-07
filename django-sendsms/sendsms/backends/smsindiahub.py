# -*- coding: utf-8 -*-

from django.conf import settings

import requests

from sendsms.backends.base import BaseSmsBackend

SMSINDIAHUB_API_URL = "https://cloud.smsindiahub.in/api/mt/SendSMS"
SMSINDIAHUB_API_KEY = getattr(settings, "SENDSMS_SMSINDIAHUB_API_KEY", "")
SMSINDIAHUB_ENABLE_UNICODE = getattr(
    settings, "SENDSMS_SMSINDIAHUB_ENABLE_UNICODE", True
)


class SmsBackend(BaseSmsBackend):
    """
    SMSIndianHub gateway backend. (https://www.smsindiahub.in/)
    Docs in https://www.smsindiahub.in/api/india/

    Settings::

        SENDSMS_BACKEND = 'sendsms.backends.smsindiahub.SmsBackend'
        SENDSMS_SMSINDIAHUB_API_KEY = 'xxx'
        SENDSMS_SMSINDIAHUB_ENABLE_UNICODE = True (default)

    Usage::

        from sendsms import api
        api.send_sms(
            body='I can haz txt', from_phone='+41791111111', to=['+41791234567']
        )

    """

    def send_messages(self, messages):
        for m in messages:
            params = {
                "APIKey": SMSINDIAHUB_API_KEY,
                "senderid": m.from_phone,
                "channel": "Trans",
                "DCS": "0",
                "flashsms": "0",
                "number": m.to,
                "text": m.body,
            }
            if SMSINDIAHUB_ENABLE_UNICODE:
                params["DCS"] = 8

            response = requests.get(SMSINDIAHUB_API_URL, params=params)

        if response.status_code != 200 or response.json().get("ErrorCode") != "000":
            if self.fail_silently:
                return False
            raise Exception(
                "Error: %d: %s"
                % (response.status_code, response.content.decode("utf-8"))
            )

        return True
