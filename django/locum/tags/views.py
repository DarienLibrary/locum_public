from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Label, Tag
from .serializers import LabelSerializer, TagSerializer
from harvest.models import BibliographicRecord


class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all()

    def list(self, request):
        labels = Label.objects.order_by()
        resp = LabelSerializer(instance=labels, many=True).data
        return Response(resp, status=status.HTTP_200_OK)

    def create(self, request):
        value = request.data.get('value', None)
        if value:
            try:
                label = Label.objects.get(value=value)
                return Response(status=status.HTTP_409_CONFLICT)
            except Label.DoesNotExist:
                label = Label(value=value)
                label.save()
                return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        pass

    def update(self, request, pk=None):
        value = request.data.get('value', None)
        if value:
            try:
                label = Label.objects.get(pk=pk)
                label.value = value
                label.save()
                return Response(status=status.HTTP_200_OK)
            except Label.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        try:
            label = Label.objects.get(pk=pk)
            label.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Label.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()

    def list(self, request):
        tags = Tag.objects.order_by()
        resp = TagSerializer(instance=tags, many=True).data
        return Response(resp, status=status.HTTP_200_OK)

    def create(self, request):
        ils_id = request.data.get('ils_id', None)
        label_id = request.data.get('label_id', None)
        if ils_id and label_id:
            try:
                label = Label.objects.get(pk=label_id)
            except Label.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            try:
                bib_record = BibliographicRecord.objects.get(ils_id=ils_id)
            except BibliographicRecord.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        tags = Tag.objects.filter(
            label__id=label.id,
            bib_record__id=bib_record.id
        )
        if tags:
            return Response(status=status.HTTP_409_CONFLICT)
        else:
            tag = Tag(
                label=label,
                bib_record=bib_record,
            )
            tag.save()
            return Response(status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        try:
            tag = Tag.objects.get(pk=pk)
            tag.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Tag.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)