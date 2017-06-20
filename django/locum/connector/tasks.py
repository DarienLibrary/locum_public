from collections import OrderedDict

import dateutil.parser

from celery import shared_task, chord
from django.conf import settings
from django.utils import timezone

import re
from datetime import datetime, timedelta

from .models import Token
from . import queries as polaris
from .mods import convert_to_mods

@shared_task
def get_bib(bnum, pdb=None, mods=False):
    if not pdb:
        pdb = polaris.Database()
    row = pdb.get_bib_record(bnum)
    if row:
        polaris_bib = parse_bib(row, pdb, mods)
    else:
        polaris_bib = None
    return polaris_bib


def get_bibs(bib_ids=[]):
    pdb = polaris.Database()
    if not bib_ids:
        bib_ids = get_bib_record_ids(pdb)
    for bnum in bib_ids:
        yield get_bib(bnum, pdb)


def get_bib_record_ids(pdb=None):
    if not pdb:
        pdb = polaris.Database()
    rows = pdb.get_bib_record_ids()
    for row in rows:
        yield row['BibliographicRecordID']


def get_bib_record_id_for_item(item_id, pdb=None):
    if not pdb:
        pdb = polaris.Database()
    return pdb.get_bib_record_id_for_item(item_id)


def parse_bib(row, pdb=None, mods=True):
    if not pdb:
        pdb = polaris.Database()
    bib = {}
    bib['bnum'] = row['bnum']
    bib['ils_id'] = bib['bnum']
    cleaned_lang = re.sub('[^A-Za-z]', '', row['lang'])
    if cleaned_lang in marc_lang_codes.keys():
        bib['lang'] = marc_lang_codes[cleaned_lang]
    else:
        bib['lang'] = None
    bib['suppress'] = not bool(row['suppress'])
    if row.get('author', ''):
        bib['author_full'] = row['author']
        bib['browse_author'] = bib['author_full']
    if row.get('title', ''):
        bib['title_full'] = row['title']
        bib['browse_title'] = bib['title_full']
    bib['call_num'] = row['call_number']
    bib['pub_year'] = row['pub_year']
    bib['precedence'] = row['precedence']
    bib['age'] = get_age(bib['bnum'], pdb)
    bib['format_abbr'] = row['format_abbr']
    bib['mat_code'] = get_mat_code(bib['bnum'], pdb)
    bib['abs_mat_type'] = get_abstract_mat_code(bib['mat_code'], bib['format_abbr'])
    bib['abs_mat_code'] = bib['abs_mat_type']
    bib['bookgroup'] = is_book_grouped(bib['mat_code'])
    if mods:
        bib.update(get_MODS_details(bib['bnum'], pdb))
    else:
        bib.update(get_MARC_details(bib['bnum'], pdb))
    return bib


def get_mat_code(bnum, pdb=None):
    if not pdb:
        pdb = polaris.Database()
    mat_codes = list(
        set([row['MaterialTypeID'] for row in pdb.get_mat_types(bnum)]))
    return mat_codes


def is_book_grouped(mat_codes):
    return 15 in mat_codes


def get_abstract_mat_code(mat_codes, format_abbr):
    i_to_am_mapping = settings.CONNECTOR['polaris']['item_to_abstract_material_mapping']
    m_to_i_mapping = settings.CONNECTOR['polaris']['material_to_item_mapping']
    if mat_codes:
        if str(mat_codes[0]) in i_to_am_mapping.keys():
            return i_to_am_mapping[str(mat_codes[0])]
    else:
        if format_abbr in m_to_i_mapping.keys():
            return i_to_am_mapping[str(m_to_i_mapping[format_abbr])]
        else:
            return i_to_am_mapping["0"]


def get_MARC_details(bnum, pdb=None):
    if not pdb:
        pdb = polaris.Database()
    MARC_details = {}
    subjects = {}
    isbns = []
    authors = []
    contributors = []
    for row in pdb.get_bib_tags(bnum):

        # work
        if row['TagNumber'] == 24 and row['Subfield'] == 'a':
            res = re.match(r'DLW(.*)', row['Data'])
            if res:
                MARC_details['work_id'] = res.group(1)

        # author
        if row['TagNumber'] == 100 and row['Subfield'] == 'a':
            author = None
            names = [re.sub(r'[^\w\-\'\ ]', '', name.strip())
                     for name in re.split('[,/]', row['Data'])]
            if len(names) == 1:
                author = names[0]
            elif len(names) > 1:
                author = '{0} {1}'.format(names[1], names[0])
            if author:
                authors.append(author)

        # all contributors
        if row['TagNumber'] in [100, 110, 111, 700, 710, 711] and row['Subfield'] == 'a':
            contributor = None
            names = [re.sub(r'[^\w\-\'\ ]', '', name.strip())
                     for name in re.split('[,/]', row['Data'])]
            if len(names) == 1:
                contributor = names[0]
            elif len(names) > 1:
                contributor = '{0} {1}'.format(names[1], names[0])
            if contributor:
                contributors.append(contributor)

        # title
        if (row['TagNumber'] == 245
                and row['Subfield'] == 'a'
                and not MARC_details.get('title')):
            MARC_details['title'] = row['Data']

        # subtitle
        if row['TagNumber'] == 245 and row['Subfield'] == 'b':
            MARC_details['subtitle'] = row['Data']

        # part
        if row['TagNumber'] == 245 and row['Subfield'] == 'p':
            MARC_details['part'] = row['Data']

        # part_num
        if row['TagNumber'] == 245 and row['Subfield'] == 'n':
            MARC_details['part_num'] = row['Data']

        # subject
        if ((row['TagNumber'] in [600, 610, 611, 630, 648, 650, 651]
            and row['Subfield'] in ['a', 'x', 'v'])
                or (row['TagNumber'] == 655 and row['Subfield'] == 'a')):
            sequence = subjects.get(row['Sequence'], [])
            if not sequence:
                subjects[row['Sequence']] = sequence
            sequence.append(
                re.sub(r'[^\w0-9 .]', '', row['Data']))

        if ((row['TagNumber'] == 856 and row['Subfield'] == 'u')
                or (row['TagNumber'] == 37 and row['Subfield'] == 'a')):
            provider_indicators = {
                'hoopla':
                    r'https://www\.hoopladigital\.com/title/(\d+)$',
                'bibliotheca':
                    r'^http://.*/library/darienlibrary-document_id-([\w]+)$',
                'overdrive':
                    r'^(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})$',
            }
            for provider, exp in provider_indicators.items():
                m = re.search(exp, row['Data'])
                if m:
                    MARC_details['provider'] = provider
                    if provider in ['bibliotheca', 'overdrive', 'hoopla']:
                        MARC_details['provider_id'] = m.group(1)
                    break

    if authors:
        MARC_details['author'] = authors[0]
    MARC_details['subject'] = []
    for subject in subjects.values():
        MARC_details['subject'].append(' - '.join(subject))
    MARC_details['isbn'] = isbns
    MARC_details['contributors'] = contributors

    return MARC_details


def get_MODS_details(bnum, pdb=None):

    class Dictlist(dict):
        def __setitem__(self, key, value):
            try:
                self[key]
            except KeyError:
                super(Dictlist, self).__setitem__(key, [])
            self[key].append(value)

    if not pdb:
        pdb = polaris.Database()
    marc = Dictlist()
    field = OrderedDict()
    tag_id = None
    tag_num = None
    for row in pdb.get_bib_tags(bnum):
        if not tag_id or tag_id != row['BibliographicTagID']:
            if field and tag_num:
                marc[tag_num] = field
            tag_id = row['BibliographicTagID']
            field = OrderedDict()
            field['ind1'] = row['IndicatorOne']
            field['ind2'] = row['IndicatorTwo']
        field[row['Subfield']] = row['Data']
        tag_num = row['TagNumber']
    if field:
        marc[row['TagNumber']] = field

    mods = convert_to_mods(marc)
    return mods


def get_age(bib_id, pdb=None):
    if not pdb:
        pdb = polaris.Database()
    abbrs = [row["Abbreviation"] for row in pdb.get_collection_abbrs(bib_id)]
    ages = set([])
    record_ages = settings.CONNECTOR['polaris']['record_ages']
    for abbr in abbrs:
        for age, expr in record_ages.items():
            if re.match(expr, abbr):
                ages.add(age)
    if ages:
        return list(ages)
    else:
        return ["unspecified"]


@shared_task
def get_changes():
    pdb = polaris.Database()
    rows = pdb.get_changed_bib_records()
    res = {}
    for row in rows:
        res[row['BibliographicRecordID']] = convert_MARC_datetime(row['MARCModificationDate'])
    return res


def get_bib_id_changes():
    id_changes = {}
    seen = set([])
    pdb = polaris.Database()
    changes = pdb.get_bib_record_id_updates()
    changes_mapping = {}
    for result in changes:
        changes_mapping.update(
            {result["NewBibRecordID"]: result["OldBibRecordID"]})
    keys = list(changes_mapping.keys())
    keys.sort(reverse=True)
    for key in keys:
        if key not in seen:
            seed = key
            while changes_mapping.get(key):
                key = changes_mapping[key]
                seen.add(key)
                id_changes.update({key: seed})
    return id_changes


def get_availability(bib_id):
    pdb = polaris.Database()
    res = pdb.get_item_availability(bib_id)
    available = 0
    holdable = 0
    items_by_group = {}
    for row in res:
        group = '{}_{}'.format(row["MaterialType"], row["LoanPeriodCodeID"])
        item_availability = items_by_group.get(group, {
            "locations": [],
            "count": 0,
            "available_count": 0,
            "holdable_count": 0,
            "holdable": False,
            "mat_code": row["MaterialType"],
        })

        item_availability["count"] += row["TotalItems"]
        item_availability["available_count"] += row["AvailableItems"]
        item_availability["holdable_count"] += row["HoldableItems"]
        item_availability["holdable"] = bool(item_availability["holdable_count"])

        collection = row["Collection"]
        call_number = row["CallNumber"]
        due_date = row["DueDate"]
        if due_date:
            due_date = timezone.make_aware(due_date)
        current_location = None
        locations = item_availability['locations']

        for location in locations:
            if (collection == location['collection'] and
                    call_number == location['call_number']):
                current_location = location
        if current_location:
            current_location["count"] += row["TotalItems"]
            current_location["available_count"] += row["AvailableItems"]
            current_location["holdable_count"] += row["HoldableItems"]
            if current_location["due_date"] and due_date:
                current_location["due_date"] = min(
                    current_location["due_date"],
                    due_date
                )
            else:
                current_location["due_date"] = None
        else:
            current_location = {
                'collection': collection,
                'call_number': call_number,
                'holdable_count': row["HoldableItems"],
                'available_count': row["AvailableItems"],
                'count': row["TotalItems"],
                'due_date': due_date
            }
            locations.append(current_location)
        available += row["AvailableItems"]
        holdable += row["HoldableItems"]
        items_by_group.update({group: item_availability})

        for group, item_availability in items_by_group.items():
            locations = item_availability["locations"]
            locations.sort(key=lambda location: (
                -int(bool(location["available_count"])),
                -int('storage' not in str(location["collection"]).lower()),
                -location["available_count"],))
            item_availability.update({
                "location": {
                    "collection": locations[0]["collection"],
                    "call_number": locations[0]["call_number"],
                }
            })
        item_groups = list(items_by_group.values())
        item_groups.sort(
            key=lambda group: (
                -group["holdable_count"],
                group["mat_code"],
            )
        )

    if res:
        availibility = {
            "success": True,
            "can_checkout": available > 0,
            "can_hold": holdable > 0,
            "available_count": available,
            "holdable_count": holdable,
            "holds_count": pdb.get_hold_count(bib_id),
            "items_by_group": item_groups,
        }
    else:
        availibility = {
            "success": False
        }
    return availibility


def validate_patron(barcode, email):
    pdb = polaris.Database()
    resp = pdb.validate_patron(barcode)
    if resp and resp['email'] and email.lower() == resp['email'].lower():
        resp.update({"valid": True})
        return resp
    else:
        return {"valid": False}


def _get_token():
    username = settings.CONNECTOR['polaris']['staff_user']
    password = settings.CONNECTOR['polaris']['staff_password']
    papi = polaris.PAPI()
    res = papi.authenticateStaffUser(
        domain='library',
        username=username,
        password=password)
    if res.status_code == 200:
        res = res.json()
        access_token = res.get('AccessToken')
        access_secret = res.get('AccessSecret')
        token_expiration = json_timestamp_to_datetime(res.get('AuthExpDate'))
        if access_token and access_secret:
            token = Token(
                id=1,
                access_token=access_token,
                access_secret=access_secret,
                token_expiration=token_expiration)
            token.save()
            return token


def authenticate_staff():
    try:
        token = Token.objects.get(pk=1)
        if token.is_expired():
            token = _get_token()
    except Token.DoesNotExist:
        token = _get_token()
    if token:
        return {
            'access_token': token.access_token,
            'access_secret': token.access_secret
        }


def search_patron(patron_name):
    token = authenticate_staff()
    if token and token.get('access_token'):
        query = re.sub(',', '', patron_name)
        papi = polaris.PAPI()
        res = papi.patronSearch(
            accessToken=token['access_token'],
            accessSecret=token['access_secret'],
            params={'q': 'PATNL={}'.format(query)})
        if res.status_code == 200:
            res = res.json()
            patrons = []
            for patron in res.get('PatronSearchRows', []):
                patron_id = patron.get('PatronID')
                if patron_id:
                    patrons.append(get_patron_basic_data(patron_id))
            resp = {
                'patrons': patrons,
                'success': True
            }
            return resp
    return {'success': False}



def get_patron_barcode_to_id_mapping():
    pdb = polaris.Database()
    rows = pdb.get_patrons()
    resp = {}
    for row in rows:
        resp.update({row["barcode"]: row["patron_id"]})
    return resp


def is_held(bib_id, pdb=None):
    if not pdb:
        pdb = polaris.Database()
    res = pdb.get_hold_count(bib_id)
    return bool(res)


def patron_exixsts(patron_id):
    pdb = polaris.Database()
    if pdb.patron_exixst(patron_id):
        return True
    else:
        return False


def get_patron(patron_id):
    pdb = polaris.Database()
    return pdb.get_patron(patron_id)


def get_patron_overdue_count(patron_barcode):
    count = 0
    papi = polaris.PAPI()
    token = authenticate_staff()
    if token and token.get('access_token'):
        raw_checkout_res = papi.patronItemsOutGet(
            patron_barcode,
            token['access_secret'],
            'all',
            accessToken=token['access_token'])
        if raw_checkout_res.status_code == 200:
            checkout_res = raw_checkout_res.json()
            checkouts = checkout_res.get('PatronItemsOutGetRows', [])
            for checkout in checkouts:
                if json_timestamp_to_datetime(
                        checkout['CheckOutDate']) < datetime.now():
                    count += 1
        return count


def get_patron_fines(patron_barcode):
    token = authenticate_staff()
    if token and token.get('access_token'):
        papi = polaris.PAPI()
        raw_res = papi.patronAccountGet(
            patron_barcode,
            token['access_secret'],
            'outstanding',
            accessToken=token['access_token'])
        if raw_res.status_code == 200:
            resp = {
                'fines': [],
                'success': True
            }
            res = raw_res.json()
            fines = res.get('PatronAccountGetRows', [])
            for fine in fines:
                if fine['TransactionTypeDescription'] == 'Charge':
                    due_date = fine['DueDate']
                    if due_date is not None:
                        due_date = json_timestamp_to_datetime(due_date)
                    details = {
                        'item_id': fine['ItemID'],
                        'ils_id': fine['BibID'],
                        'transaction_date': json_timestamp_to_datetime(
                            fine['TransactionDate']),
                        'fee_description': fine['FeeDescription'],
                        'outstanding_amount': fine['OutstandingAmount'],
                        'title': fine['Title'],
                        'author': fine['Author'],
                        'due_date': due_date
                    }
                    resp['fines'].append(details)
        else:
            resp = {
                'success': False
            }
        return resp


def get_patron_circulation(patron_barcode):
    papi = polaris.PAPI()
    pdb = polaris.Database()
    # get checkouts data
    token = authenticate_staff()
    if token and token.get('access_token'):
        raw_checkout_res = papi.patronItemsOutGet(
            patron_barcode,
            token['access_secret'],
            'all',
            accessToken=token['access_token'])
        if raw_checkout_res.status_code == 200:
            resp = {
                "checkouts": [],
                "holds": [],
                "success": True,
                "provider_elapsed_time": raw_checkout_res.elapsed
            }
            checkout_res = raw_checkout_res.json()
            checkouts = checkout_res.get('PatronItemsOutGetRows', [])
            for checkout in checkouts:
                due_date = json_timestamp_to_datetime(checkout['DueDate'])

                renewable = (not is_held(checkout['BibID'], pdb) and
                             checkout['RenewalCount'] < checkout['RenewalLimit'])
                details = {
                    'author': checkout.get('Author', ''),
                    'title': checkout.get('Title', ''),
                    'checkout_date': json_timestamp_to_datetime(
                        checkout['CheckOutDate']),
                    'due_date': due_date,
                    'ils_id': checkout['BibID'],
                    'is_overdue': timezone.now() > due_date,
                    'is_renewable': renewable,
                    'item_id': checkout['ItemID'],
                }
                resp["checkouts"].append(details)
        # get holds data
            raw_hold_res = papi.patronHoldRequestsGet(
                patron_barcode,
                token['access_secret'],
                'all',
                accessToken=token['access_token']
            )
            if raw_hold_res.status_code == 200:
                resp['provider_elapsed_time'] += raw_hold_res.elapsed
                hold_res = raw_hold_res.json()
                holds = hold_res.get('PatronHoldRequestsGetRows', [])
                for hold in holds:
                    status = hold['StatusDescription']
                    if status not in ['Cancelled', 'Not Supplied']:
                        pick_up_by_date = hold.get('PickupByDate', None)
                        if pick_up_by_date:
                            is_ready = True
                            pick_up_by_date = json_timestamp_to_datetime(
                                pick_up_by_date)
                        else:
                            is_ready = False
                        details = {
                            'author': hold.get('Author', ''),
                            'title': hold.get('Title', ''),
                            'hold_list_position': hold['QueuePosition'],
                            'hold_placed_date': json_timestamp_to_datetime(
                                hold['ActivationDate']),
                            'ils_id': hold['BibID'],
                            'request_id': hold['HoldRequestID'],
                            'status': status,
                            'expiration_date': pick_up_by_date,
                            'is_ready': is_ready,
                            'is_suspended': status == 'Inactive',
                        }
                        resp["holds"].append(details)
                return resp
    return {"success": False}


def patron_place_hold(patron_id, bib_id):
    resp = {
        "success": False,
    }
    papi = polaris.PAPI()
    raw_res = papi.holdRequestCreate(
        patronID=patron_id,
        bibID=bib_id,
        pickupOrgID='3',
        workstationID='1',
        userID='3',
        requestingOrgID='3')
    if raw_res.status_code == 200:
        res = raw_res.json()
        print(res)
        if res.get("StatusType"):
            while res["StatusType"] == 3:
                requestGUID = res.get('RequestGUID')
                txnGroupQualifier = res.get('TxnGroupQualifer') #misspelling returned by the api
                txnQualifier = res.get('TxnQualifier')
                state = res.get('StatusValue')
                print(requestGUID, txnQualifier, txnGroupQualifier, state)
                raw_res = papi.holdRequestReply(
                    requestGUID=requestGUID,
                    txnGroupQualifier=txnGroupQualifier,
                    txnQualifier=txnQualifier,
                    requestingOrgID='3',
                    answer='1',
                    state=state)
                if raw_res.status_code == 200:
                    res = raw_res.json()
                    print(res)
                else:
                    return {"success": False}
            if res.get("StatusType") == 1:
                return {"success": False}
            if res.get("StatusType") == 2:
                return {"success": True}
    return resp

@shared_task
def patron_renew_item(patron_barcode, item):
    token = authenticate_staff()
    if token and token.get('access_token'):
        papi = polaris.PAPI()
        raw_res = papi.itemRenew(
            patronBarcode=patron_barcode,
            patronPassword=token['access_secret'],
            itemID=item,
            logonBranchID='3',
            logonUserID='3',
            logonWorkstationID='1',
            ignoreOverrideErrors='true',
            accessToken=token['access_token'])
        if raw_res.status_code == 200:
            resp = {
                "items": [],
                "success": True,
                # "provider_elapsed_time": float(raw_res.elapsed)
            }
            res = raw_res.json()['ItemRenewResult']

            renews = res.get('DueDateRows', [])
            for item in renews:
                details = {
                    'item_id': item['ItemRecordID'],
                    'due_date': str(json_timestamp_to_datetime(item['DueDate'])),
                    'renewed': True,
                    'errors': [],
                }
                resp["items"].append(details)

            unreneweds = res.get('BlockRows', [])
            error_dict = {}
            for item in unreneweds:
                item_id = item['ItemRecordID']
                errors = error_dict.get(item_id, [])
                error = re.sub(r', not allowed to renew', '', item['ErrorDesc'])
                errors.append(error)
                error_dict[item_id] = errors
            for item_id, errors in error_dict.items():
                details = {
                    'item_id': item_id,
                    'due_date': None,
                    'renewed': False,
                    'errors': errors,
                }
                resp["items"].append(details)
            return resp
        elif item_id == '0':
            resp = {
                'success': False,
            }
        else:
            resp = {
                'success': False,
                'item_id': item_id,
            }
        return resp


def patron_renew_items(patron_barcode, items):
    # header = [
    #     patron_renew_item.s(patron_barcode, item)
    #     for item in items]
    # resp = chord(header)(chain_renews.s())
    # resp = resp.get()
    try:
        resp = chain_renews(
            [patron_renew_item(patron_barcode, item)
             for item in items])
    except:
        return {'success': False}
    papi = polaris.PAPI()
    # get checkouts data
    token = authenticate_staff()
    if token and token.get('access_token'):
        raw_checkout_res = papi.patronItemsOutGet(
            patron_barcode,
            token['access_secret'],
            'all',
            accessToken=token['access_token'])
        if raw_checkout_res.status_code == 200:
            due_dates = {}
            checkout_res = raw_checkout_res.json()
            checkouts = checkout_res.get('PatronItemsOutGetRows', [])
            for checkout in checkouts:
                due_date = json_timestamp_to_datetime(checkout['DueDate'])
                details = {checkout['ItemID']: due_date}
                due_dates.update(details)
            for item in resp['items']:
                if item['due_date'] is None:
                    item['due_date'] = due_dates.get(item['item_id'], None)
        return resp


def patron_cancel_hold(patron_barcode, request_id):
    papi = polaris.PAPI()
    token = authenticate_staff()
    if token and token.get('access_token'):
        res = papi.holdRequestCancel(
            patronBarcode=patron_barcode,
            patronPassword=token['access_secret'],
            requestID=request_id,
            workstationID='1',
            userID='3',
            accessToken=token['access_token'])
        if res.status_code == 200 and not res.json().get('PAPIErrorCode', True):
            return {"success": True}
        else:
            return {"success": False}


def patron_update_hold(patron_barcode, request_id, activity, activation_date=timezone.now()):
    papi = polaris.PAPI()
    activation_date_str = str(int(activation_date.timestamp()))
    token = authenticate_staff()
    if token and token.get('access_token'):
        res = papi.holdRequestSuspend(
            patronBarcode=patron_barcode,
            patronPassword=token['access_secret'],
            requestID=request_id,
            activity=activity,
            userID='3',
            activationDate=activation_date_str,
            accessToken=token['access_token'])
        resp = {
            "items": [],
            "success": True
        }
        if res.status_code == 200 and not res.json().get('PAPIErrorCode', True):
            rows = res.json().get('HoldRequestActivationRows', [])
            for row in rows:
                if request_id == '0':
                    r_id = row['SysHoldRequestID']
                else:
                    r_id = request_id
                item = {
                    "success": True,
                    "expiration_date": json_timestamp_to_datetime(
                        row['NewExpirationDate']),
                    "activation_date": json_timestamp_to_datetime(
                        row['NewActivationDate']),
                    "request_id": r_id
                }
                resp['items'].append(item)
            return resp
        return {"success": False}


def patron_suspend_hold(patron_barcode, request_id, activation_date):
    return patron_update_hold(
        patron_barcode,
        request_id,
        'inactive',
        activation_date)


def patron_suspend_all_holds(patron_barcode, activation_date):
    return patron_update_hold(
        patron_barcode,
        '0',
        'inactive',
        activation_date)


def patron_reactivate_hold(patron_barcode, request_id):
    return patron_update_hold(
        patron_barcode,
        request_id,
        'active')


def patron_reactivate_all_holds(patron_barcode):
    return patron_update_hold(
        patron_barcode,
        '0',
        'active')

@shared_task
def chain_renews(renews):
    items = []
    success = False
    # provider_elapsed_time = 0
    for renew in renews:
        # provider_elapsed_time += renew['provider_elapsed_time']
        if renew['success']:
            items += renew['items']
            success = True
        else:
            item = {
                'item_id': renew['item_id'],
                'due_date': None,
                'renewed': False,
                'errors': ['failed connection'],
            }
            items += item
    resp = {
        'success': success,
        'items': items
    }
    return resp


def patron_renew_all_items(patron_barcode):
    return patron_renew_items(patron_barcode, ['0'])


def get_patron_basic_data(patron_id):
    pdb = polaris.Database()
    res = pdb.get_patron_basic_data(patron_id)
    if res:
        phones = {
            'home': res.get('home'),
            'cell': res.get('cell'),
        }
        address = {
            'street_line_two': res.get('street_line_two'),
            'county': res.get('county'),
            'city': res.get('city'),
            'postal_code': res.get('postal_code'),
            'country': res.get('country'),
            'state': res.get('state'),
            'street_line_one': res.get('street_line_one'),
        }
        resp = {
            'address': address,
            'phones': phones,
            'success': True,
            'first_name': res.get('first_name'),
            'last_name': res.get('last_name'),
            'email': res.get('email'),
            'birthdate': res.get('birthdate'),
            'checkout_history': bool(res.get('checkout_history'))
        }
        return resp
    else:
        return {'success': False}


def update_patron_basic_data(patron_barcode, patron_id, **kwargs):
    papi = polaris.PAPI()
    token = authenticate_staff()
    if token and token.get('access_token'):
        res = papi.patronUpdate(
            patronBarcode=patron_barcode,
            patronPassword=token['access_secret'],
            logonBranchID='3',
            logonUserID='3',
            logonWorkstationID='1',
            readingListFlag=kwargs.get('checkout_history'),
            emailAddress=kwargs.get('email'),
            phoneVoice1=kwargs.get('home'),
            accessToken=token['access_token']
        )
        cell = kwargs.get('cell')
        if cell:
            pdb = polaris.Database()
            pdb.update_patron_cellphone(patron_id, cell)
        if res.status_code == 200:
            return {"success": True}
        else:
            return {"success": False}


def get_patron_checkout_history(patron_id, limit, offset):
    pdb = polaris.Database()
    history = {}
    checkouts = pdb.get_patron_reading_history(patron_id, -1, 0)
    count = len(checkouts)
    if offset < count:
        if offset + limit < count:
            checkouts = checkouts[offset:offset + limit]
        else:
            checkouts = checkouts[offset:]
    else:
        checkouts = []
    next_offset = None
    prev_offset = None
    if offset + limit <= count:
        next_offset = offset + limit
    if offset - limit >= 0:
        prev_offset = offset - limit
    results = []
    for checkout in checkouts:
        details = {
            'checkout_date': checkout['DateCheckedOut'],
            'title': checkout.get('Title', ''),
            'author': checkout.get('Author', ''),
            'ils_id': checkout['BibliographicRecordID'],
            'id': checkout['PatronReadingHistoryID'],
        }
        results.append(details)
    history.update({
        "results": results,
        "count": count,
        "next": next_offset,
        "previous": prev_offset})
    return history


def delete_patron_checkout_history_item(patron_id, reading_history_id):
    pdb = polaris.Database()
    pdb.delete_patron_reading_history_item(patron_id, reading_history_id)


def clear_patron_checkout_history(patron_barcode):
    papi = polaris.PAPI()
    token = authenticate_staff()
    if token and token.get('access_token'):
        raw_resp = papi.patronReadingHistoryClear(
            patron_barcode,
            token['access_secret'],
            accessToken=token['access_token'])
        if raw_resp.status_code == 200:
            return {"success": True}
        else:
            return {"success": False}


def suppress_bibs(bib_ids):
    pdb = polaris.Database()
    pdb.suppress_bibs(bib_ids)


def add_work_id_to_bib(assignment):
    pdb = polaris.Database()
    bib_ids = set(get_bib_record_ids(pdb))
    for bib_id, work_id in assignment.items():
        if bib_id in bib_ids:
            subfield_id = pdb.get_work_id_subfield_id(bib_id)
            if subfield_id:
                pdb.update_work_id(work_id, subfield_id)
            else:
                pdb.add_work_id_to_bib(bib_id, work_id)


def get_manual_notes():
    notes = {}
    pdb = polaris.Database()
    rows = pdb.get_manual_notes()
    for row in rows:
        _, key = row['Data'].split('>')
        bib_id = row['BibliographicRecordID']
        bib_ids = notes.get(key, [])
        bib_ids.append(bib_id)
        notes[key] = bib_ids
    return notes


def json_timestamp_to_datetime(json_timestamp):
    m = re.search(r'^/Date\((\d+)([\+\-])(\d{4})\)/$', json_timestamp)
    d = timezone.make_aware(datetime.utcfromtimestamp(int(m.group(1)[:-3])))
    offset = timedelta(hours=int(m.group(3)[:2]), minutes=int(m.group(3)[2:]))
    if m.group(2) == '+':
        return d + offset
    else:
        return d - offset


def convert_MARC_datetime(s):
    t = '{}-{}-{} {}:{}'.format(s[:4], s[4:6], s[6:8], s[8:10], s[10:12])
    return timezone.make_aware(dateutil.parser.parse(t))


def isbn10_check_digit(isbn):
    assert len(isbn) == 9
    sum = 0
    for i in range(len(isbn)):
        c = int(isbn[i])
        w = i + 1
        sum += w * c
    r = sum % 11
    if r == 10:
        return 'X'
    else:
        return str(r)


def isbn13_check_digit(isbn):
    assert len(isbn) == 12
    sum = 0
    for i in range(len(isbn)):
        c = int(isbn[i])
        if i % 2:
            w = 3
        else:
            w = 1
        sum += w * c
    r = 10 - (sum % 10)
    if r == 10:
        return '0'
    else:
        return str(r)


def isbn_convert_10_to_13(isbn):
    assert len(isbn) == 10
    prefix = '978' + isbn[:-1]
    check = isbn13_check_digit(prefix)
    return prefix + check

marc_lang_codes = {
    "aar": "Afar",
    "abk": "Abkhaz",
    "ace": "Achinese",
    "ach": "Acoli",
    "ada": "Adangme",
    "ady": "Adygei",
    "afa": "Afroasiatic",
    "afh": "Afrihili",
    "afr": "Afrikaans",
    "ain": "Ainu",
    "ajm": "Aljamía",
    "aka": "Akan",
    "akk": "Akkadian",
    "alb": "Albanian",
    "ale": "Aleut",
    "alg": "Algonquian",
    "alt": "Altai",
    "amh": "Amharic",
    "ang": "English, Old",
    "anp": "Angika",
    "apa": "Apache languages",
    "ara": "Arabic",
    "arc": "Aramaic",
    "arg": "Aragonese",
    "arm": "Armenian",
    "arn": "Mapuche",
    "arp": "Arapaho",
    "art": "Artificial",
    "arw": "Arawak",
    "asm": "Assamese",
    "ast": "Bable",
    "ath": "Athapascan",
    "aus": "Australian languages",
    "ava": "Avaric",
    "ave": "Avestan",
    "awa": "Awadhi",
    "aym": "Aymara",
    "aze": "Azerbaijani",
    "bad": "Banda languages",
    "bai": "Bamileke languages",
    "bak": "Bashkir",
    "bal": "Baluchi",
    "bam": "Bambara",
    "ban": "Balinese",
    "baq": "Basque",
    "bas": "Basa",
    "bat": "Baltic",
    "bej": "Beja",
    "bel": "Belarusian",
    "bem": "Bemba",
    "ben": "Bengali",
    "ber": "Berber",
    "bho": "Bhojpuri",
    "bih": "Bihari",
    "bik": "Bikol",
    "bin": "Edo",
    "bis": "Bislama",
    "bla": "Siksika",
    "bnt": "Bantu",
    "bos": "Bosnian",
    "bra": "Braj",
    "bre": "Breton",
    "btk": "Batak",
    "bua": "Buriat",
    "bug": "Bugis",
    "bul": "Bulgarian",
    "bur": "Burmese",
    "byn": "Bilin",
    "cad": "Caddo",
    "cai": "Central American Indian",
    "cam": "Khmer",
    "car": "Carib",
    "cat": "Catalan",
    "cau": "Caucasian",
    "ceb": "Cebuano",
    "cel": "Celtic",
    "cha": "Chamorro",
    "chb": "Chibcha",
    "che": "Chechen",
    "chg": "Chagatai",
    "chi": "Chinese",
    "chk": "Chuukese",
    "chm": "Mari",
    "chn": "Chinook jargon",
    "cho": "Choctaw",
    "chp": "Chipewyan",
    "chr": "Cherokee",
    "chu": "Church Slavic",
    "chv": "Chuvash",
    "chy": "Cheyenne",
    "cmc": "Chamic languages",
    "cop": "Coptic",
    "cor": "Cornish",
    "cos": "Corsican",
    "cpe": "Creoles and Pidgins, English-based",
    "cpf": "Creoles and Pidgins, French-based",
    "cpp": "Creoles and Pidgins, Portuguese-based",
    "cre": "Cree",
    "crh": "Crimean Tatar",
    "crp": "Creoles and Pidgins",
    "csb": "Kashubian",
    "cus": "Cushitic",
    "cze": "Czech",
    "dak": "Dakota",
    "dan": "Danish",
    "dar": "Dargwa",
    "day": "Dayak",
    "del": "Delaware",
    "den": "Slavey",
    "dgr": "Dogrib",
    "din": "Dinka",
    "div": "Divehi",
    "doi": "Dogri",
    "dra": "Dravidian",
    "dsb": "Lower Sorbian",
    "dua": "Duala",
    "dum": "Dutch, Middle",
    "dut": "Dutch",
    "dyu": "Dyula",
    "dzo": "Dzongkha",
    "efi": "Efik",
    "egy": "Egyptian",
    "eka": "Ekajuk",
    "elx": "Elamite",
    "eng": "English",
    "enm": "English, Middle",
    "epo": "Esperanto",
    "esk": "Eskimo languages",
    "esp": "Esperanto",
    "est": "Estonian",
    "eth": "Ethiopic",
    "ewe": "Ewe",
    "ewo": "Ewondo",
    "fan": "Fang",
    "fao": "Faroese",
    "far": "Faroese",
    "fat": "Fanti",
    "fij": "Fijian",
    "fil": "Filipino",
    "fin": "Finnish",
    "fiu": "Finno-Ugrian",
    "fon": "Fon",
    "fre": "French",
    "fri": "Frisian",
    "frm": "French, Middle",
    "fro": "French, Old",
    "frr": "North Frisian",
    "frs": "East Frisian",
    "fry": "Frisian",
    "ful": "Fula",
    "fur": "Friulian",
    "gaa": "Gã",
    "gae": "Scottish Gaelix",
    "gag": "Galician",
    "gal": "Oromo",
    "gay": "Gayo",
    "gba": "Gbaya",
    "gem": "Germanic",
    "geo": "Georgian",
    "ger": "German",
    "gez": "Ethiopic",
    "gil": "Gilbertese",
    "gla": "Scottish Gaelic",
    "gle": "Irish",
    "glg": "Galician",
    "glv": "Manx",
    "gmh": "German, Middle High",
    "goh": "German, Old High",
    "gon": "Gondi",
    "gor": "Gorontalo",
    "got": "Gothic",
    "grb": "Grebo",
    "grc": "Greek, Ancient",
    "gre": "Greek, Modern",
    "grn": "Guarani",
    "gsw": "Swiss German",
    "gua": "Guarani",
    "guj": "Gujarati",
    "gwi": "Gwich'in",
    "hai": "Haida",
    "hat": "Haitian French Creole",
    "hau": "Hausa",
    "haw": "Hawaiian",
    "heb": "Hebrew",
    "her": "Herero",
    "hil": "Hiligaynon",
    "him": "Western Pahari languages",
    "hin": "Hindi",
    "hit": "Hittite",
    "hmn": "Hmong",
    "hmo": "Hiri Motu",
    "hrv": "Croatian",
    "hsb": "Upper Sorbian",
    "hun": "Hungarian",
    "hup": "Hupa",
    "iba": "Iban",
    "ibo": "Igbo",
    "ice": "Icelandic",
    "ido": "Ido",
    "iii": "Sichuan Yi",
    "ijo": "Ijo",
    "iku": "Inuktitut",
    "ile": "Interlingue",
    "ilo": "Iloko",
    "ina": "Interlingua",
    "inc": "Indic",
    "ind": "Indonesian",
    "ine": "Indo-European",
    "inh": "Ingush",
    "int": "Interlingua",
    "ipk": "Inupiaq",
    "ira": "Iranian",
    "iri": "Irish",
    "iro": "Iroquoian",
    "ita": "Italian",
    "jav": "Javanese",
    "jbo": "Lojban",
    "jpn": "Japanese",
    "jpr": "Judeo-Persian",
    "jrb": "Judeo-Arabic",
    "kaa": "Kara-Kalpak",
    "kab": "Kabyle",
    "kac": "Kachin",
    "kal": "Kalâtdlisut",
    "kam": "Kamba",
    "kan": "Kannada",
    "kar": "Karen languages",
    "kas": "Kashmiri",
    "kau": "Kanuri",
    "kaw": "Kawi",
    "kaz": "Kazakh",
    "kbd": "Kabardian",
    "kha": "Khasi",
    "khi": "Khoisan",
    "khm": "Khmer",
    "kho": "Khotanese",
    "kik": "Kikuyu",
    "kin": "Kinyarwanda",
    "kir": "Kyrgyz",
    "kmb": "Kimbundu",
    "kok": "Konkani",
    "kom": "Komi",
    "kon": "Kongo",
    "kor": "Korean",
    "kos": "Kosraean",
    "kpe": "Kpelle",
    "krc": "Karachay-Balkar",
    "krl": "Karelian",
    "kro": "Kru",
    "kru": "Kurukh",
    "kua": "Kuanyama",
    "kum": "Kumyk",
    "kur": "Kurdish",
    "kus": "Kusaie",
    "kut": "Kootenai",
    "lad": "Ladino",
    "lah": "Lahndā",
    "lam": "Lamba",
    "lan": "Occitan",
    "lao": "Lao",
    "lap": "Sami",
    "lat": "Latin",
    "lav": "Latvian",
    "lez": "Lezgian",
    "lim": "Limburgish",
    "lin": "Lingala",
    "lit": "Lithuanian",
    "lol": "Mongo-Nkundu",
    "loz": "Lozi",
    "ltz": "Luxembourgish",
    "lua": "Luba-Lulua",
    "lub": "Luba-Katanga",
    "lug": "Ganda",
    "lui": "Luiseño",
    "lun": "Lunda",
    "luo": "Luo",
    "lus": "Lushai",
    "mac": "Macedonian",
    "mad": "Madurese",
    "mag": "Magahi",
    "mah": "Marshallese",
    "mai": "Maithili",
    "mak": "Makasar",
    "mal": "Malayalam",
    "man": "Mandingo",
    "mao": "Maori",
    "map": "Austronesian",
    "mar": "Marathi",
    "mas": "Maasai",
    "max": "Manx",
    "may": "Malay",
    "mdf": "Moksha",
    "mdr": "Mandar",
    "men": "Mende",
    "mga": "Irish, Middle",
    "mic": "Micmac",
    "min": "Minangkabau",
    "mis": "Miscellaneous languages",
    "mkh": "Mon-Khmer",
    "mla": "Malagasy",
    "mlg": "Malagasy",
    "mlt": "Maltese",
    "mnc": "Manchu",
    "mni": "Manipuri",
    "mno": "Manobo languages",
    "moh": "Mohawk",
    "mol": "Moldavian",
    "mon": "Mongolian",
    "mos": "Mooré",
    "mul": "Multiple languages",
    "mun": "Munda",
    "mus": "Creek",
    "mwl": "Mirandese",
    "mwr": "Marwari",
    "myn": "Mayan languages",
    "myv": "Erzya",
    "nah": "Nahuatl",
    "nai": "North American Indian",
    "nap": "Neapolitan Italian",
    "nau": "Nauru",
    "nav": "Navajo",
    "nbl": "Ndebele",
    "nde": "Ndebele",
    "ndo": "Ndonga",
    "nds": "Low German",
    "nep": "Nepali",
    "new": "Newari",
    "nia": "Nias",
    "nic": "Niger-Kordofanian",
    "niu": "Niuean",
    "nno": "Norwegian",
    "nob": "Norwegian",
    "nog": "Nogai",
    "non": "Old Norse",
    "nor": "Norwegian",
    "nqo": "N'Ko",
    "nso": "Northern Sotho",
    "nub": "Nubian languages",
    "nwc": "Newari, Old",
    "nya": "Nyanja",
    "nym": "Nyamwezi",
    "nyn": "Nyankole",
    "nyo": "Nyoro",
    "nzi": "Nzima",
    "oci": "Occitan",
    "oji": "Ojibwa",
    "ori": "Oriya",
    "orm": "Oromo",
    "osa": "Osage",
    "oss": "Ossetic",
    "ota": "Turkish, Ottoman",
    "oto": "Otomian languages",
    "paa": "Papuan",
    "pag": "Pangasinan",
    "pal": "Pahlavi",
    "pam": "Pampanga",
    "pan": "Panjabi",
    "pap": "Papiamento",
    "pau": "Palauan",
    "peo": "Old Persian",
    "per": "Persian",
    "phi": "Philippine",
    "phn": "Phoenician",
    "pli": "Pali",
    "pol": "Polish",
    "pon": "Pohnpeian",
    "por": "Portuguese",
    "pra": "Prakrit languages",
    "pro": "Provençal",
    "pus": "Pushto",
    "que": "Quechua",
    "raj": "Rajasthani",
    "rap": "Rapanui",
    "rar": "Rarotongan",
    "roa": "Romance",
    "roh": "Raeto-Romance",
    "rom": "Romani",
    "rum": "Romanian",
    "run": "Rundi",
    "rup": "Aromanian",
    "rus": "Russian",
    "sad": "Sandawe",
    "sag": "Sango",
    "sah": "Yakut",
    "sai": "South American Indian",
    "sal": "Salishan languages",
    "sam": "Samaritan Aramaic",
    "san": "Sanskrit",
    "sao": "Samoan",
    "sas": "Sasak",
    "sat": "Santali",
    "scc": "Serbian",
    "scn": "Sicilian Italian",
    "sco": "Scots",
    "scr": "Croatian",
    "sel": "Selkup",
    "sem": "Semitic",
    "sga": "Irish, Old",
    "sgn": "Sign languages",
    "shn": "Shan",
    "sho": "Shona",
    "sid": "Sidamo",
    "sin": "Sinhalese",
    "sio": "Siouan",
    "sit": "Sino-Tibetan",
    "sla": "Slavic",
    "slo": "Slovak",
    "slv": "Slovenian",
    "sma": "Southern Sami",
    "sme": "Northern Sami",
    "smi": "Sami",
    "smj": "Lule Sami",
    "smn": "Inari Sami",
    "smo": "Samoan",
    "sms": "Skolt Sami",
    "sna": "Shona",
    "snd": "Sindhi",
    "snh": "Sinhalese",
    "snk": "Soninke",
    "sog": "Sogdian",
    "som": "Somali",
    "son": "Songhai",
    "sot": "Sotho",
    "spa": "Spanish",
    "srd": "Sardinian",
    "srn": "Sranan",
    "srp": "Serbian",
    "srr": "Serer",
    "ssa": "Nilo-Saharan",
    "sso": "Sotho",
    "ssw": "Swazi",
    "suk": "Sukuma",
    "sun": "Sundanese",
    "sus": "Susu",
    "sux": "Sumerian",
    "swa": "Swahili",
    "swe": "Swedish",
    "swz": "Swazi",
    "syc": "Syriac",
    "syr": "Syriac, Modern",
    "tag": "Tagalog",
    "tah": "Tahitian",
    "tai": "Tai",
    "taj": "Tajik",
    "tam": "Tamil",
    "tar": "Tatar",
    "tat": "Tatar",
    "tel": "Telugu",
    "tem": "Temne",
    "ter": "Terena",
    "tet": "Tetum",
    "tgk": "Tajik",
    "tgl": "Tagalog",
    "tha": "Thai",
    "tib": "Tibetan",
    "tig": "Tigré",
    "tir": "Tigrinya",
    "tiv": "Tiv",
    "tkl": "Tokelauan",
    "tlh": "Klingon",
    "tli": "Tlingit",
    "tmh": "Tamashek",
    "tog": "Tonga",
    "ton": "Tongan",
    "tpi": "Tok Pisin",
    "tru": "Truk",
    "tsi": "Tsimshian",
    "tsn": "Tswana",
    "tso": "Tsonga",
    "tsw": "Tswana",
    "tuk": "Turkmen",
    "tum": "Tumbuka",
    "tup": "Tupi languages",
    "tur": "Turkish",
    "tut": "Altaic",
    "tvl": "Tuvaluan",
    "twi": "Twi",
    "tyv": "Tuvinian",
    "udm": "Udmurt",
    "uga": "Ugaritic",
    "uig": "Uighur",
    "ukr": "Ukrainian",
    "umb": "Umbundu",
    "urd": "Urdu",
    "uzb": "Uzbek",
    "vai": "Vai",
    "ven": "Venda",
    "vie": "Vietnamese",
    "vol": "Volapük",
    "vot": "Votic",
    "wak": "Wakashan languages",
    "wal": "Wolayta",
    "war": "Waray",
    "was": "Washoe",
    "wel": "Welsh",
    "wen": "Sorbian",
    "wln": "Walloon",
    "wol": "Wolof",
    "xal": "Oirat",
    "xho": "Xhosa",
    "yao": "Yao",
    "yap": "Yapese",
    "yid": "Yiddish",
    "yor": "Yoruba",
    "ypk": "Yupik languages",
    "zap": "Zapotec",
    "zbl": "Blissymbolics",
    "zen": "Zenaga",
    "zha": "Zhuang",
    "znd": "Zande languages",
    "zul": "Zulu",
    "zun": "Zuni",
    "zza": "Zaza"}
