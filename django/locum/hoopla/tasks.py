from django.utils import timezone
from datetime import datetime
import pytz


from .hoopla import HooplaAPI


def parse_datetime(timestamp):
    dt = pytz.utc.localize(datetime.utcfromtimestamp(timestamp))
    return dt
    #return timezone.localtime(dt)


def get_availability(item_id):
    details = {
        "success": True,
        "can_checkout": True,
        "can_hold": False,
        "holds_count": 0
    }
    return details


def get_circulation(barcode):
    hapi = HooplaAPI()
    raw_res = hapi.get_patron_circulation(barcode)
    if raw_res and raw_res.status_code == 200:
        resp = {
            "checkouts": [],
            "holds": [],
            "provider_elaspsed_time": raw_res.elapsed
        }
        checkouts = raw_res.json()
        print(checkouts)
        for checkout in checkouts:
            details = {
                'checkout_date': parse_datetime(checkout['borrowed']),
                'expiration_date': parse_datetime(checkout['due']),
                'provider': 'hoopla',
                'provider_id': checkout['contentId'],
            }
            resp['checkouts'].append(details)
        resp.update({'success': True})
    else:
        resp = {'success': False}
    return resp


def checkout(barcode, item_id):
    hapi = HooplaAPI()
    res = hapi.checkout(item_id, barcode)
    if res.status_code == 500:
        resp = {"success": True}
    else:
        resp = {"success": False}
        try:
            resp.update(res.json())
        except:
            pass
    return resp


def checkin(barcode, item_id):
    hapi = HooplaAPI()
    res = hapi.checkin(item_id, barcode)
    if res and res.status_code == 204:
        return {"success": True}
    else:
        return {"success": False}
