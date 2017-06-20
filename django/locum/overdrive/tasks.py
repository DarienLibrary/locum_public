from django.utils import timezone
import dateutil.parser

from .overdrive import OverdriveAPI


def parse_datetime(overdrive_datetime):
    dt = dateutil.parser.parse(overdrive_datetime)
    return timezone.localtime(dt)

def get_circulation(barcode):
    overdriveapi = OverdriveAPI(barcode)
    # get checkouts data
    checkout_res = overdriveapi.get_checkouts()
    if not checkout_res['success']:
        return checkout_res
    resp = {
        "checkouts": [],
        "holds": [],
        "success": True,
    }
    checkouts = checkout_res.get("checkouts", [])
    for checkout in checkouts:
        details = {
            'checkout_date': parse_datetime(checkout["checkoutDate"]),
            'expiration_date': parse_datetime(checkout["expires"]),
            'provider': 'overdrive',
            'provider_id': checkout['reserveId'],
        }
        resp["checkouts"].append(details)
    # get holds data
    hold_res = overdriveapi.get_holds()
    if not hold_res['success']:
        return hold_res
    holds = hold_res.get("holds", [])
    for hold in holds:
        raw_exp_date = hold.get("holdExpires", None)
        if raw_exp_date:
            expiration_date = parse_datetime(raw_exp_date)
            is_ready = True
        else:
            expiration_date = None
            is_ready = False
        details = {
            'hold_list_position': hold["holdListPosition"],
            'hold_placed_date': parse_datetime(hold["holdPlacedDate"]),
            'is_ready': is_ready,
            'expiration_date': expiration_date,
            'is_suspended': bool(hold.get('holdSuspension', False)),
            'provider': 'overdrive',
            'provider_id': hold['reserveId'],
        }
        resp["holds"].append(details)
    return resp


def checkout(barcode, item_id):
    overdriveapi = OverdriveAPI(barcode)
    res = overdriveapi.checkout(item_id)
    if res['success']:
        return {'success': True}
    else:
        return res


def checkin(barcode, item_id):
    overdriveapi = OverdriveAPI(barcode)
    res = overdriveapi.checkin(item_id)
    if res['success']:
        return {'success': True}
    else:
        return res


def place_hold(barcode, item_id, email):
    overdriveapi = OverdriveAPI(barcode)
    res = overdriveapi.place_hold(item_id, email)
    if res['success']:
        return {'success': True}
    else:
        return res

def suspend_hold(barcode, item_id, email):
    overdriveapi = OverdriveAPI(barcode)
    res = overdriveapi.suspend_hold(item_id, email)
    if res['success']:
        return {
            "success": True,
            "items": [{
                "item_id": item_id,
                "success": True
            }]
        }
    else:
        return res

def reactivate_hold(barcode, item_id):
    overdriveapi = OverdriveAPI(barcode)
    res = overdriveapi.reactivate_hold(item_id)
    if res['success']:
        return {
            "success": True,
            "items": [{
                "item_id": item_id,
                "success": True
            }]
        }
    else:
        return res

def cancel_hold(barcode, item_id):
    overdriveapi = OverdriveAPI(barcode)
    res = overdriveapi.cancel_hold(item_id)
    if res['success']:
        return {'success': True}
    else:
        return res

def get_availability(item_id):
    overdriveapi = OverdriveAPI()
    res = overdriveapi.get_item_availability(item_id)
    if res['success']:
        item = res
        resp = {
            "can_checkout": item['available'],
            "can_hold": not item['available'],
            "holds_count": int(item['numberOfHolds']),
            "success": True,
        }
        return resp
    else:
        return res
