from rest_framework import serializers

from .models import Wish, Rating, Review
from harvest.serializers import BibSerializer
from harvest.models import WorkRecord


class WorkSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkRecord
        fields = [
            "id",
            "title",
            "author",
        ]


class WishSerializer(serializers.ModelSerializer):
    work_record = WorkSerializer(read_only=True)
    patron_id = serializers.SerializerMethodField()

    def get_patron_id(self, obj):
        return obj.patron.patron_id

    class Meta:
        model = Wish
        fields = [
            'id',
            'patron_id',
            'date_created',
            'work_record',
        ]


class RatingSerializer(serializers.ModelSerializer):
    bib_record = BibSerializer(read_only=True)
    patron_id = serializers.SerializerMethodField()

    def get_patron_id(self, obj):
        return obj.patron.patron_id

    class Meta:
        model = Rating
        fields = [
            'id',
            'date_created',
            'bib_record',
            'rating',
        ]


class ReviewSerializer(serializers.ModelSerializer):
    bib_record = BibSerializer(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'date_created',
            'bib_record',
            'title',
            'body',
        ]
