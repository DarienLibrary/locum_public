from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from .models import Wish, Review, Rating
from .serializers import WishSerializer, RatingSerializer, ReviewSerializer
from patron.models import Patron
from harvest.models import BibliographicRecord, WorkRecord


class WishViewSet(viewsets.ModelViewSet):
    queryset = Wish.objects.all()
    paginator = LimitOffsetPagination()

    bad_resp = {"success": False}
    good_resp = {"success": True}

    def list(self, request):
        patron_id = request.query_params.get('patron_id', None)
        if patron_id:
            try:
                patron = Patron.objects.get(patron_id=patron_id)
            except Patron.DoesNotExist:
                return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(self.bad_resp, status=status.HTTP_400_BAD_REQUEST)

        queryset = Wish.objects.filter(patron__patron_id=patron_id)
        paginated_queryset = self.paginator.paginate_queryset(queryset, self.request, view=self)
        serializer = WishSerializer(paginated_queryset, many=True)
        resp = self.paginator.get_paginated_response(serializer.data)
        resp.data.update(self.good_resp)
        resp.data['wishes'] = resp.data['results']
        return resp

    def create(self, request):
        patron_id = request.data.get('patron_id', None)
        work_id = request.data.get('work_id', None)
        if patron_id and work_id:
            try:
                patron = Patron.objects.get(patron_id=patron_id)
            except Patron.DoesNotExist:
                patron = None
            try:
                work_record = WorkRecord.objects.get(id=work_id)
            except WorkRecord.DoesNotExist:
                work_record = None
        else:
            return Response(self.bad_resp, status=status.HTTP_400_BAD_REQUEST)

        if patron and work_record:
            wishes = Wish.objects.filter(
                patron__id=patron.id,
                work_record__id=work_record.id)
            if wishes:
                return Response(self.bad_resp, status=status.HTTP_409_CONFLICT)
            else:
                wish = Wish(
                    patron=patron,
                    work_record=work_record,
                )
                wish.save()
                return Response(self.good_resp, status=status.HTTP_201_CREATED)
        else:
            return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk=None):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        patron_id = request.data.get('patron_id', None)
        if patron_id:
            try:
                patron = Patron.objects.get(patron_id=patron_id)
            except Patron.DoesNotExist:
                return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(self.bad_resp, status=status.HTTP_400_BAD_REQUEST)
        try:
            wish = Wish.objects.filter(patron__patron_id=patron_id).get(pk=pk)
            wish.delete()
            return Response(self.good_resp, status=status.HTTP_200_OK)
        except Wish.DoesNotExist:
            return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)


class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()

    bad_resp = {"success": False}
    good_resp = {"success": True}

    def list(self, request):
        patron_id = request.query_params.get('patron_id', None)
        if patron_id:
            try:
                patron = Patron.objects.get(patron_id=patron_id)
            except Patron.DoesNotExist:
                return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(self.bad_resp, status=status.HTTP_400_BAD_REQUEST)

        ratings = Rating.objects.filter(patron__patron_id=patron_id)
        resp = {"ratings": RatingSerializer(instance=ratings, many=True).data}
        resp.update(self.good_resp)
        return Response(resp, status=status.HTTP_200_OK)

    def create(self, request):
        patron_id = request.data.get('patron_id', None)
        ils_id = request.data.get('ils_id', None)
        score = request.data.get('rating', None)
        if patron_id and ils_id and type(score) == int:
            try:
                patron = Patron.objects.get(patron_id=patron_id)
            except Patron.DoesNotExist:
                patron = None
            try:
                bib_record = BibliographicRecord.objects.get(ils_id=ils_id)
            except BibliographicRecord.DoesNotExist:
                bib_record = None
        else:
            return Response(self.bad_resp, status=status.HTTP_400_BAD_REQUEST)

        if patron and bib_record:
            ratings = Rating.objects.filter(
                patron__id=patron.id,
                bib_record__id=bib_record.id
            )
            if ratings:
                return Response(self.bad_resp, status=status.HTTP_409_CONFLICT)
            else:
                rating = Rating(
                    patron=patron,
                    bib_record=bib_record,
                    rating=score,
                )
                rating.save()
                return Response(self.good_resp, status=status.HTTP_201_CREATED)
        else:
            return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk=None):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        try:
            rating = Rating.objects.get(pk=pk)
        except Rating.DoesNotExist:
            return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)

        score = request.data.get('rating', None)
        if score:
            rating.rating = score
            rating.save()
            return Response(self.good_resp, status=status.HTTP_200_OK)
        else:
            return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        try:
            rating = Rating.objects.get(pk=pk)
            rating.delete()
            return Response(self.good_resp, status=status.HTTP_200_OK)
        except Rating.DoesNotExist:
            return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()

    bad_resp = {"success": False}
    good_resp = {"success": True}

    def list(self, request):
        patron_id = request.query_params.get('patron_id', None)
        if patron_id:
            try:
                patron = Patron.objects.get(patron_id=patron_id)
            except Patron.DoesNotExist:
                return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(self.bad_resp, status=status.HTTP_400_BAD_REQUEST)

        reviews = Review.objects.filter(patron__patron_id=patron_id)
        resp = {"reviews": ReviewSerializer(instance=reviews, many=True).data}
        resp.update(self.good_resp)
        return Response(resp, status=status.HTTP_200_OK)

    def create(self, request):
        patron_id = request.data.get('patron_id', None)
        ils_id = request.data.get('ils_id', None)
        body = request.data.get('body', None)
        title = request.data.get('title', None)
        if patron_id and ils_id and body and title:
            try:
                patron = Patron.objects.get(patron_id=patron_id)
            except Patron.DoesNotExist:
                patron = None
            try:
                bib_record = BibliographicRecord.objects.get(ils_id=ils_id)
            except BibliographicRecord.DoesNotExist:
                bib_record = None
        else:
            return Response(self.bad_resp, status=status.HTTP_400_BAD_REQUEST)

        if patron and bib_record:
            reviews = Review.objects.filter(
                patron__id=patron.id,
                bib_record__id=bib_record.id
            )
            if reviews:
                return Response(self.bad_resp, status=status.HTTP_409_CONFLICT)
            else:
                review = Review(
                    patron=patron,
                    bib_record=bib_record,
                    body=body,
                    title=title,
                )
                review.save()
                return Response(self.good_resp, status=status.HTTP_201_CREATED)
        else:
            return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk=None):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)

        body = request.data.get('body', None)
        title = request.data.get('title', None)
        if body:
            review.body = body
        if title:
            review.title = title
        if body or title:
            review.save()
            return Response(self.good_resp, status=status.HTTP_200_OK)
        else:
            return Response(self.bad_resp, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        try:
            review = Review.objects.get(pk=pk)
            review.delete()
            return Response(status=status.HTTP_200_OK)
        except Review.DoesNotExist:
            return Response(self.bad_resp, status=status.HTTP_404_NOT_FOUND)