from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework import status

from .models import WorkRecord, BibliographicRecord
from .serializers import WorkSerializer, LongWorkSerializer, BibSerializer


class WorkRecordViewSet(ViewSet):

    def handle_exception(self, exc):
        return Response({"details": str(exc)})

    queryset = WorkRecord.objects.all()

    def retrieve(self, request, pk=None):
        try:
            work_record = WorkRecord.objects.get(pk=pk)
        except WorkRecord.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        resp = WorkSerializer(instance=work_record).data
        return Response(resp)

    @detail_route(methods=['get'])
    def long(self, request, pk):
        try:
            work_record = WorkRecord.objects.get(pk=pk)
        except WorkRecord.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        resp = LongWorkSerializer(instance=work_record).data
        return Response(resp)

class BibliographicRecordViewSet(ViewSet):

    def handle_exception(self, exc):
        return Response({"details": str(exc)})

    queryset = BibliographicRecord.objects.all()

    def retrieve(self, request, pk=None):
        try:
            bib_record = BibliographicRecord.objects.get(ils_id=pk)
        except BibliographicRecord.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        resp = BibSerializer(instance=bib_record).data
        return Response(resp)

    @detail_route(methods=['get'])
    def availability(self, request, pk):
        try:
            bib_record = BibliographicRecord.objects.get(ils_id=pk)
        except BibliographicRecord.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        resp = bib_record.get_availability()
        return Response(resp)
