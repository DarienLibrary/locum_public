from rest_framework import serializers

from .models import BibliographicRecord, WorkRecord
import connector.tasks
import connector.mods


class BibSerializer(serializers.ModelSerializer):
    locum_id = serializers.SerializerMethodField('get_id')

    class Meta:
        model = BibliographicRecord
        fields = [
            'locum_id',
            'ils_id',
            'browse_author',
            'browse_title',
            'provider',
            'provider_id',
            'format_abbr',
            'abs_mat_code',
        ]

    def get_id(self, obj):
        return obj.id


class WorkSerializer(serializers.ModelSerializer):
    bib_records = BibSerializer(many=True, read_only=True)
    title = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()

    class Meta:
        model = WorkRecord
        fields = [
            "id",
            "title",
            "author",
            "bib_records",
        ]

    def get_title(self, obj):
        if obj.primary_bib_record:
            return obj.primary_bib_record.browse_title
        else:
            return obj.title

    def get_author(self, obj):
        if obj.primary_bib_record:
            return obj.primary_bib_record.author
        else:
            return obj.author


class LongWorkSerializer(WorkSerializer):
    details = serializers.SerializerMethodField()

    class Meta:
        model = WorkRecord
        fields = [
            "id",
            "title",
            "author",
            "bib_records",
            "details",
        ]

    def get_details(self, obj):
        bibs = []
        for ils_id in obj.bib_records.values_list('ils_id', flat=True):
            bibs.append(connector.tasks.get_bib(ils_id, mods=True))
        genres = connector.mods.consolidate_content(bibs, 'genres')
        subjects = connector.mods.consolidate_content(bibs, 'subjects')
        abstract = connector.mods.get_longest_exemplar(bibs, 'abstracts', 'abstract')
        details = {
            'bib_records': bibs,
            'genres': genres,
            'subjects': subjects,
            'abstract': abstract,
        }
        return details
