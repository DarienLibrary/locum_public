from django.conf import settings
import requests
from datetime import timedelta
from django.utils import timezone

from .models import Token


class HooplaAPI(object):

    def __init__(self):
        self.library_id = settings.HOOPLA['library_id']
        self.root_uri = settings.HOOPLA['root_uri']
        self.username = settings.HOOPLA['username']
        self.password = settings.HOOPLA['password']
        self.has_token = False

        try:
            token = Token.objects.get(pk=1)
            if not token.is_expired():
                self.access_token = token.access_token
                self.token_type = token.token_type
                self.has_token = True
            elif self.get_token():
                token.access_token = self.access_token
                token.token_type = self.token_type
                token.token_expiration = self.token_expiration
                token.save()
        except Token.DoesNotExist:
            if self.get_token():
                token = Token(
                    id=1,
                    access_token=self.access_token,
                    token_type=self.token_type,
                    token_expiration=self.token_expiration)
                token.save()

    def _exec_request(self, http_method, suffix_uri, **kwargs):
        # This is the heart of the API wrapper. All the Hoopla API methods
        # take their method specific input and parse it and call this method
        # which then constructs and sends the appropriate request.
        if not self.has_token and not self.get_token():
            return {'success': False}
        else:
            res = None
            uri = self.root_uri + suffix_uri
            headers = {
                'Content-type': 'application/json',
                'Accept': 'application/json',
                'Authorization': '{} {}'.format(
                    self.token_type.title(),
                    self.access_token
                )
            }
            try:
                res = requests.request(http_method, uri, headers=headers)
            except requests.exceptions.RequestException:
                pass
            return res

    def get_token(self, **kwargs):
        http_method = 'POST'
        suffix_uri = '/get-token'
        uri = self.root_uri + suffix_uri
        raw_res = requests.request(
            http_method,
            uri,
            auth=(self.username, self.password))
        if raw_res is not None and raw_res.status_code == 200:
            res = raw_res.json()
            access_token = res.get('access_token')
            token_type = res.get('token_type')
            expiration = timezone.now() + timedelta(seconds=int(res.get('expires_in'))-60)
            if access_token and token_type:
                self.access_token = access_token
                self.token_type = token_type
                self.token_expiration = expiration
                self.has_token = True
        return self.has_token

    def checkout(self, item_id, patron_barcode, **kwargs):
        http_method = 'POST'
        suffix_uri = '/libraries/{library_id}/patrons/{patron_barcode}/{item_id}'.format(
            library_id=self.library_id,
            item_id=item_id,
            patron_barcode=patron_barcode)
        return self._exec_request(http_method, suffix_uri, **kwargs)

    def checkin(self, item_id, patron_barcode, **kwargs):
        http_method = 'DELETE'
        suffix_uri = '/libraries/{library_id}/patrons/{patron_barcode}/{item_id}'.format(
            library_id=self.library_id,
            item_id=item_id,
            patron_barcode=patron_barcode)
        return self._exec_request(http_method, suffix_uri, **kwargs)

    def get_patron_circulation(self, patron_barcode, **kwargs):
        http_method = 'GET'
        suffix_uri = '/libraries/{library_id}/patrons/{patron_barcode}/checkouts/current'.format(
            library_id=self.library_id,
            patron_barcode=patron_barcode)
        return self._exec_request(http_method, suffix_uri, **kwargs)
