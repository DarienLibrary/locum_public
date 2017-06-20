from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework import status
import dateutil.parser

from rest_framework.pagination import LimitOffsetPagination

import harvest.tasks
import connector.tasks
from .models import Patron


class CheckoutViewSet(ViewSet):
    bad_resp = {"success": False}
    good_resp = {"success": True}

    def destroy(self, request, pk=None):
        reading_history_id = pk
        patron_id = request.data.get('patron_id')
        if reading_history_id and patron_id:
            connector.tasks.delete_patron_checkout_history_item(
                patron_id,
                reading_history_id
            )
            return Response(self.good_resp, status=status.HTTP_200_OK)
        else:
            return Response(self.bad_resp, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['delete'])
    def purge(self, request):
        patron_id = request.data.get('patron_id')
        if patron_id:
            try:
                patron = Patron.objects.get(patron_id=patron_id)
            except Patron.DoesNotExist:
                patron = Patron(patron_id=patron_id)
            ils_details = patron.get_ils_details()
            if ils_details:
                patron.save()
                resp = patron.clear_checkout_history()
                if resp['success']:
                    return Response(self.good_resp, status=status.HTTP_204_NO_CONTENT)
        return Response(self.bad_resp, status=status.HTTP_400_BAD_REQUEST)


class PatronViewSet(ViewSet):

    paginator = LimitOffsetPagination()

    def handle_exception(self, exc):
        return Response({"details": str(exc)})

    queryset = Patron.objects.all()

    def get_patron(self, patron_id):
        try:
            patron = Patron.objects.get(patron_id=patron_id)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=patron_id)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
        return ils_details

    def retrieve(self, request, pk=None):
        patron = self.get_patron(patron_id=pk)
        if not patron:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            resp = connector.tasks.get_patron_basic_data(pk)
            return Response(resp)

    def partial_update(self, request, pk=None):
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
        else:
            Response({'success': False}, status=status.HTTP_404_NOT_FOUND)
        kwargs = {
            k: request.data.get(k)
            for k in [
                'email',
                'home',
                'cell',
                'checkout_history']
        }
        resp = patron.update_ils_basic_data(**kwargs)
        if resp and resp['success']:
            return Response(resp, status=status.HTTP_200_OK)
        return Response(resp, status=status.HTTP_404_NOT_FOUND)

    @list_route(methods=['get'])
    def search(self, request):
        patron_name = request.query_params.get('patron_name')
        if not patron_name:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            resp = connector.tasks.search_patron(patron_name)
            return Response(resp, status=status.HTTP_200_OK)

    @list_route(methods=['post'])
    def validate(self, request):
        barcode = request.data.get('barcode', None)
        email = request.data.get('email', None)
        if barcode is not None and email is not None:
            resp = connector.tasks.validate_patron(barcode, email)
            if resp and resp['valid']:
                patron_id = resp['patron_id']
                try:
                    patron = Patron.objects.get(patron_id=patron_id)
                except Patron.DoesNotExist:
                    patron = Patron(patron_id=patron_id)
                    patron.save()
                return Response(resp, status=status.HTTP_200_OK)
            else:
                return Response(resp, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['get'])
    def circulation(self, request, pk=None):
        ils_details = self.get_patron(pk)
        provider = request.query_params.get('provider', None)
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            resp = patron.get_circulation(provider)
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def checkout(self, request, pk=None):
        provider_id = request.data.get('provider_id', None)
        provider = request.query_params.get('provider', None)
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            resp = patron.checkout(provider, provider_id)
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def place_hold(self, request, pk=None):
        ils_id = request.data.get('ils_id', None)
        provider_id = request.data.get('provider_id', None)
        provider = request.query_params.get('provider', None)
        if not provider_id and ils_id:
            provider_id = ils_id
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            resp = patron.place_hold(provider, provider_id)
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def checkin(self, request, pk=None):
        provider_id = request.data.get('provider_id', None)
        provider = request.query_params.get('provider', None)
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            resp = patron.checkin(provider, provider_id)
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def cancel_hold(self, request, pk=None):
        provider_id = request.data.get('provider_id', None)
        request_id = request.data.get('request_id', None)
        if not provider_id and request_id:
            provider_id = request_id
        provider = request.query_params.get('provider', None)
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            resp = patron.cancel_hold(provider, provider_id)
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def suspend_hold(self, request, pk=None):
        provider = request.query_params.get('provider', None)
        provider_id = request.data.get('provider_id', None)
        request_id = request.data.get('request_id', None)
        if not provider_id and request_id:
            provider_id = request_id
        activation_date_str = request.data.get('activation_date', None)
        if activation_date_str:
            activation_date = dateutil.parser.parse(activation_date_str)
        else:
            activation_date = None
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            resp = patron.suspend_hold(provider, provider_id, activation_date)
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def suspend_all_holds(self, request, pk=None):
        activation_date_str = request.data.get('activation_date', None)
        if activation_date_str:
            activation_date = dateutil.parser.parse(activation_date_str)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            resp = patron.suspend_all_holds(activation_date)
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def reactivate_hold(self, request, pk=None):
        provider = request.query_params.get('provider', None)
        provider_id = request.data.get('provider_id', None)
        request_id = request.data.get('request_id', None)
        if not provider_id and request_id:
            provider_id = request_id
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            resp = patron.reactivate_hold(provider, provider_id)
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def reactivate_all_holds(self, request, pk=None):
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            resp = patron.reactivate_all_holds()
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def renew_all(self, request, pk=None):
        patron = self.get_patron(pk)
        barcode = patron['barcode']
        resp = harvest.tasks.patron_renew_all_items(barcode)
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def renew(self, request, pk=None):
        patron = self.get_patron(pk)
        barcode = patron['barcode']
        items = request.data.get('items', None)
        resp = harvest.tasks.patron_renew_items(barcode, items)
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def fines(self, request, pk=None):
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            resp = patron.get_fines()
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def balance(self, request, pk=None):
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            resp = patron.get_balance()
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def history(self, request, pk=None):
        try:
            patron = Patron.objects.get(patron_id=pk)
        except Patron.DoesNotExist:
            patron = Patron(patron_id=pk)
        ils_details = patron.get_ils_details()
        if ils_details:
            patron.save()
            limit = int(request.query_params.get('limit', 25))
            offset = int(request.query_params.get('offset', 0))
            resp = patron.get_checkout_history(limit, offset)
        return Response(resp, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def update_history(self, request, pk=None):
        return Response({"success": True}, status=status.HTTP_200_OK)
