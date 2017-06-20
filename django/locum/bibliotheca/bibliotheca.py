from django.conf import settings

from binascii import b2a_base64
from email.utils import formatdate
from hashlib import sha256
import hmac
import requests


class BibliothecaAPI(object):

    def __init__(self):
        self.library_id = settings.BIBLIOTHECA['library_id']
        self.access_id = settings.BIBLIOTHECA['access_id']
        self.access_key = settings.BIBLIOTHECA['access_key']

    def _get_signature(self, http_method, http_date, uri):
        message = '{}\n{}\n{}'.format(http_date, http_method, uri)
        hashed = hmac.new(
            self.access_key.encode('utf-8'),
            message.encode('utf-8'),
            sha256)
        return b2a_base64(hashed.digest()).decode('ascii')[:-1]

    def _exec_request(self, http_method, suffix_uri, **kwargs):
        # This is the heart of the API wrapper. All the Bibliotheca API methods
        # take their method specific input and parse it and call this method
        # which then constructs and sends the appropriate request.
        http_date = formatdate(timeval=None, localtime=False, usegmt=True)
        root_uri = settings.BIBLIOTHECA['root_uri']
        uri = root_uri + suffix_uri  # + params_suffix
        signature = self._get_signature(http_method, http_date, suffix_uri)
        headers = {
            'Content-type': 'text/xml',
            '3mcl-Datetime': http_date,
            '3mcl-Authorization': '3MCLAUTH {}:{}'.format(
                self.access_id,
                signature),
            '3mcl-APIVersion': '1.0',
        }
        data = kwargs.get('data', '')
        try:
            res = requests.request(http_method, uri, headers=headers, data=data, timeout=4)
        except requests.exceptions.RequestException:
            res = None
        return res

    def get_item_details(self, item_id, **kwargs):
        http_method = 'GET'
        patron_id = kwargs.get('patron_barcode')
        if patron_id:
            suffix_uri = '/cirrus/library/{library_id}/item/{item_id}?patronid={patron_id}'.format(
                library_id=self.library_id,
                item_id=item_id,
                patron_id=patron_id)
        else:
            suffix_uri = '/cirrus/library/{library_id}/item/{item_id}'.format(
                library_id=self.library_id, item_id=item_id)
        return self._exec_request(http_method, suffix_uri, **kwargs)

    def get_items_details(self, item_ids, **kwargs):
        http_method = 'GET'
        patron_id = kwargs.get('patron_barcode')
        if patron_id:
            suffix_uri = '/cirrus/library/{library_id}/items/{item_ids}?patronid={patron_id}'.format(
                library_id=self.library_id,
                item_ids=','.join(item_ids),
                patron_id=patron_id)
        else:
            suffix_uri = '/cirrus/library/{library_id}/items/{item_ids}'.format(
                library_id=self.library_id, item_ids=','.join(item_ids))
        return self._exec_request(http_method, suffix_uri, **kwargs)

    def checkout(self, item_id, patron_barcode, **kwargs):
        http_method = 'PUT'
        suffix_uri = '/cirrus/library/{library_id}/checkout'.format(
            library_id=self.library_id)
        data = "<CheckoutRequest><ItemId>{item_id}</ItemId><PatronId>{patron_id}</PatronId></CheckoutRequest>".format(
            item_id=item_id, patron_id=patron_barcode)
        return self._exec_request(http_method, suffix_uri, data=data, **kwargs)

    def checkin(self, item_id, patron_barcode, **kwargs):
        http_method = 'POST'
        suffix_uri = '/cirrus/library/{library_id}/checkin'.format(
            library_id=self.library_id)
        data = "<CheckinRequest><ItemId>{item_id}</ItemId><PatronId>{patron_id}</PatronId></CheckinRequest>".format(
            item_id=item_id, patron_id=patron_barcode)
        return self._exec_request(http_method, suffix_uri, data=data, **kwargs)

    def place_hold(self, item_id, patron_barcode, **kwargs):
        http_method = 'PUT'
        suffix_uri = '/cirrus/library/{library_id}/placehold'.format(
            library_id=self.library_id)
        data = "<PlaceHoldRequest><ItemId>{item_id}</ItemId><PatronId>{patron_id}</PatronId></PlaceHoldRequest>".format(
            item_id=item_id, patron_id=patron_barcode)
        return self._exec_request(http_method, suffix_uri, data=data, **kwargs)

    def cancel_hold(self, item_id, patron_barcode, **kwargs):
        http_method = 'POST'
        suffix_uri = '/cirrus/library/{library_id}/cancelhold'.format(library_id=self.library_id)
        data = "<CancelHoldRequest><ItemId>{item_id}</ItemId><PatronId>{patron_id}</PatronId></CancelHoldRequest>".format(
            item_id=item_id, patron_id=patron_barcode)
        return self._exec_request(http_method, suffix_uri, data=data, **kwargs)

    def get_patron_circulation(self, patron_barcode, **kwargs):
        http_method = 'GET'
        suffix_uri = '/cirrus/library/{library_id}/circulation/patron/{patron_id}'.format(
            library_id=self.library_id, patron_id=patron_barcode)
        return self._exec_request(http_method, suffix_uri, **kwargs)

    def get_marc(self, **kwargs):
        http_method = 'GET'
        suffix_uri = '/cirrus/library/{library_id}/data/marc/'.format(
            library_id=self.library_id)
        return self._exec_request(http_method, suffix_uri, **kwargs)
