import xmltodict

import collections
from django.utils import timezone
import pytz
import dateutil.parser

from .bibliotheca import BibliothecaAPI


def parse_datetime(bibliotheca_datetime):
    dt = pytz.utc.localize(dateutil.parser.parse(bibliotheca_datetime))
    return timezone.localtime(dt)


def get_circulation(barcode):
    bapi = BibliothecaAPI()
    raw_res = bapi.get_patron_circulation(barcode)
    if raw_res and raw_res.status_code == 200:
        resp = {
            "checkouts": [],
            "holds": [],
            "provider_elaspsed_time": raw_res.elapsed
        }
        res = xmltodict.parse(raw_res.text)
        checkouts = res['PatronCirculation'].get('Checkouts', None)
        if checkouts is None:
            checkouts = []
        elif type(checkouts['Item']) is collections.OrderedDict:
            checkouts = [checkouts['Item']]
        elif type(checkouts['Item']) is list:
            checkouts = checkouts['Item']
        for checkout in checkouts:
            details = {
                'checkout_date': parse_datetime(
                    checkout["EventStartDateInUTC"]),
                'expiration_date': parse_datetime(
                    checkout["EventEndDateInUTC"]),
                'provider': 'bibliotheca',
                'provider_id': checkout['ItemId'],
            }

            resp["checkouts"].append(details)
        holds = res['PatronCirculation'].get('Holds', None)
        if holds is None:
            holds = []
        elif type(holds['Item']) is collections.OrderedDict:
            holds = [holds['Item']]
        elif type(holds['Item']) is list:
            holds = holds['Item']
        for hold in holds:
            details = {
                'hold_list_position': hold["Position"],
                'hold_placed_date': parse_datetime(
                    hold["EventStartDateInUTC"]),
                'expiration_date': None,
                'is_ready': False,
                'provider': 'bibliotheca',
                'provider_id': hold['ItemId'],
                'is_suspended': False,
            }
            resp["holds"].append(details)
        reserves = res['PatronCirculation'].get('Reserves', None)
        if reserves is None:
            reserves = []
        elif type(reserves['Item']) is collections.OrderedDict:
            reserves = [reserves['Item']]
        elif type(holds['Item']) is list:
            reserves = reserves['Item']
        for hold in reserves:
            details = {
                'hold_list_position': hold["Position"],
                'hold_placed_date': parse_datetime(
                    hold["EventStartDateInUTC"]),
                'is_ready': True,
                'expiration_date': parse_datetime(
                    hold["EventEndDateInUTC"]),
                'provider': 'bibliotheca',
                'provider_id': hold['ItemId'],
                'is_suspended': False,
            }
            resp["holds"].append(details)
        resp.update({'success': True})
    else:
        resp = {'success': False}
    return resp


def checkout(barcode, item_id):
    bapi = BibliothecaAPI()
    res = bapi.checkout(item_id, barcode)
    if res and res.status_code == 201:
        return {"success": True}
    else:
        return {"success": False}


def checkin(barcode, item_id):
    bapi = BibliothecaAPI()
    res = bapi.checkin(item_id, barcode)
    if res and res.status_code == 200:
        return {"success": True}
    else:
        return {"success": False}


def place_hold(barcode, item_id, email):
    bapi = BibliothecaAPI()
    res = bapi.place_hold(item_id, barcode)
    if res and res.status_code == 201:
        return {"success": True}
    else:
        return {"success": False}


def cancel_hold(barcode, item_id):
    bapi = BibliothecaAPI()
    res = bapi.cancel_hold(item_id, barcode)
    if res and res.status_code == 200:
        return {"success": True}
    else:
        return {"success": False}


def get_availability(item_id):
    if item_id is not None:
        bapi = BibliothecaAPI()
        res = bapi.get_item_details(item_id)
        if res and res.status_code == 200:
            item = xmltodict.parse(res.text)['Item']
            resp = {
                "can_checkout": item['CanCheckout'] == "TRUE",
                "can_hold": item['CanHold'] == "TRUE",
                "holds_count": int(item['OnHoldCount']),
                "success": True
            }
            return resp
    return {"success": False}
