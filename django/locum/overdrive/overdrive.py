import requests
from base64 import b64encode
import json
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from .models import Token


class OverdriveAPI(object):

    def __init__(self, barcode=None):
        self.website_id = settings.OVERDRIVE['website_id']
        self.library_id = settings.OVERDRIVE['library_id']
        self.authorization_name = settings.OVERDRIVE['authorization_name']
        self.client_id = settings.OVERDRIVE['client_id']
        self.client_secret = settings.OVERDRIVE['client_secret']
        self.patron_barcode = barcode
        self.collection_id = None
        self.default_collection_id = 'v1L1BBwIAAA2U'
        self.error = None

        try:
            token = Token.objects.get(barcode=barcode)
            if not token.is_expired():
                self.access_token = token.access_token
                self.token_type = token.token_type
                self.has_token = True
            elif self.get_token():
                token.access_token = self.access_token
                token.token_type = self.token_type
                token.token_expiration = timezone.now() + timedelta(minutes=59)
                token.save()
        except Token.DoesNotExist:
            if self.get_token():
                token = Token(
                    barcode=barcode,
                    access_token=self.access_token,
                    token_type=self.token_type,
                    token_expiration=timezone.now() + timedelta(minutes=59))
                token.save()

    def _exec_request(self, http_method, root_uri, suffix_uri, **kwargs):
        # This is the heart of the API wrapper. All the Overdrive API methods
        # take their method specific input and parse it and call this method
        # which then constructs and sends the appropriate request.
        params = kwargs.get('params', {})
        if not self.has_token and not self.get_token():
            res = self.error
            resp = res.json()
            resp.update({'success': False})
            return resp
        uri = root_uri + suffix_uri
        headers = {
            'Authorization': '{token_type} {access_token}'.format(
                token_type=self.token_type.title(),
                access_token=self.access_token),
            'Content-Type': 'application/json; charset=utf-8'
        }
        data = kwargs.get('data', '')
        try:
            res = requests.request(
                http_method,
                uri,
                headers=headers,
                data=data,
                params=params,
                timeout=4)
        except requests.exceptions.RequestException:
            return {'success': False}
        if res.content:
            resp = res.json()
        else:
            resp = {}
        if 200 <= res.status_code < 300:
            resp.update({'success': True})
        else:
            resp.update({'success': False})
        return resp

    def get_token(self):
        signature = b64encode('{}:{}'.format(
            self.client_id,
            self.client_secret).encode('utf-8')).decode('ascii')
        headers = {
            'Authorization': 'Basic {signature}'.format(signature=signature),
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }
        if self.patron_barcode:
            data = "grant_type=password&username={patron_barcode}&password=[ignore]&password_required=false&scope=websiteid:{website_id} authorizationname:{authorization_name}".format(
                patron_barcode=self.patron_barcode,
                website_id=self.website_id,
                authorization_name=self.authorization_name)
            uri = "https://oauth-patron.overdrive.com/patrontoken"
        else:
            data = "grant_type=client_credentials"
            uri = "https://oauth.overdrive.com/token"
        res = requests.post(uri, headers=headers, data=data)
        if res.status_code == 200:
            token_info = res.json()
            self.access_token = token_info['access_token']
            self.token_type = token_info['token_type']
            self.has_token = True
        else:
            self.has_token = False
            self.error = res
        return self.has_token

    def get_collection_id(self):
        res = self.get_patron_data().json()
        self.collection_id = res['collectionToken']

    def get_patron_data(self):
        http_method = 'GET'
        root_uri = 'http://patron.api.overdrive.com'
        suffix_uri = '/v1/patrons/me'
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri)

    def get_item_availability(self, item_id):
        http_method = 'GET'
        root_uri = 'http://api.overdrive.com'
        # if self.patron_barcode and not self.collection_id:
        #     self.get_collection_id()
        #     collection_id = self.collection_id
        # else:
        collection_id = self.default_collection_id
        suffix_uri = '/v1/collections/{collection_id}/products/{product_id}/availability'.format(
            collection_id=collection_id,
            product_id=item_id)
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri)

    def get_checkouts(self):
        http_method = 'GET'
        root_uri = 'http://patron.api.overdrive.com'
        suffix_uri = '/v1/patrons/me/checkouts'
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri)

    def checkout(self, item_id):
        http_method = 'POST'
        root_uri = 'http://patron.api.overdrive.com'
        suffix_uri = '/v1/patrons/me/checkouts'
        data = {
            "fields": [
                {
                    "name": "reserveId",
                    "value": item_id
                }
            ]
        }
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri,
            data=json.dumps(data))

    def checkin(self, item_id):
        http_method = 'DELETE'
        root_uri = 'http://patron.api.overdrive.com'
        suffix_uri = '/v1/patrons/me/checkouts/{item_id}'.format(
            item_id=item_id)
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri)

    def get_holds(self):
        http_method = 'GET'
        root_uri = 'http://patron.api.overdrive.com'
        suffix_uri = '/v1/patrons/me/holds'
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri)

    def place_hold(self, item_id, email):
        http_method = 'POST'
        root_uri = 'http://patron.api.overdrive.com'
        suffix_uri = '/v1/patrons/me/holds'
        data = {
            "fields": [
                {
                    "name": "reserveId",
                    "value": item_id
                },
                {
                    "name": "emailAddress",
                    "value": email
                }
            ]
        }
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri,
            data=json.dumps(data))

    def suspend_hold(self, item_id, email):
        http_method = 'POST'
        root_uri = 'http://patron.api.overdrive.com'
        suffix_uri = '/v1/patrons/me/holds/{item_id}/suspension'.format(
            item_id=item_id)
        data = {
            "fields": [
                {
                    "name": "emailAddress",
                    "value": email
                },
                {
                    "name": "suspensionType",
                    "value": "indefinite"
                }
            ]
        }
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri,
            data=json.dumps(data))

    def reactivate_hold(self, item_id):
        http_method = 'DELETE'
        root_uri = 'http://patron.api.overdrive.com'
        suffix_uri = '/v1/patrons/me/holds/{item_id}/suspension'.format(
            item_id=item_id)
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri)

    def cancel_hold(self, item_id):
        http_method = 'DELETE'
        root_uri = 'http://patron.api.overdrive.com'
        suffix_uri = '/v1/patrons/me/holds/{item_id}'.format(item_id=item_id)
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri)

    def get_library(self):
        # useful for finding collections id
        http_method = 'GET'
        root_uri = 'http://integration.api.overdrive.com'
        suffix_uri = '/v1/libraries/{library_id}'.format(
            library_id=self.library_id)
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri)

    def get_bulk_metadata(self, item_ids):
        http_method = 'GET'
        root_uri = 'http://integration.api.overdrive.com'
        suffix_uri = '/v1/collections/{collection_id}/bulkmetadata?reserveIds={item_ids}'.format(
            collection_id=self.default_collection_id,
            item_ids=','.join(item_ids))
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri)

    def get_changed_items(
            self,
            last_update_time,
            minimum=True,
            offset=0,
            limit=300):
        http_method = 'GET'
        root_uri = 'http://integration.api.overdrive.com'
        suffix_uri = '/v1/collections/{collection_id}/products'.format(
            collection_id=self.default_collection_id)
        params = {
            'lastUpdateTime': last_update_time,
            'minimum': minimum,
            'limit': limit,
            'offset': offset,
        }
        return self._exec_request(
            http_method=http_method,
            root_uri=root_uri,
            suffix_uri=suffix_uri,
            params=params)
