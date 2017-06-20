from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from . import tasks


class SearchView(APIView):

    def handle_exception(self, exc):
        return Response({"details": str(exc)})

    def post(self, request, format=None):
        query = request.data.get('query', None)
        if query:
            search_type = request.data.get('type', 'keyword')
            popularity_period = request.data.get('popularity_period', 'year')
            popularity_weight = request.data.get('popularity_weight', 0.1)
            limit = request.data.get('limit', 10)
            offset = request.data.get('offset', 0)
            facets = request.data.get('facets', {})
            sort = request.data.get('sort', [])
            resp = tasks.search(
                query,
                limit,
                offset,
                search_type,
                popularity_period,
                popularity_weight,
                facets,
                sort)
            return Response(resp, status=status.HTTP_200_OK)
        return Response()


class BookListView(APIView):

    def handle_exception(self, exc):
        return Response({"details": str(exc)})

    def post(self, request, format=None):
        work_ids = request.data.get('work_ids', None)
        if work_ids is not None:
            resp = tasks.search_presentation(work_ids)
            return Response(resp, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)