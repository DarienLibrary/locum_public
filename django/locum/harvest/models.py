from celery.contrib.methods import task
from elasticsearch import Elasticsearch

from datetime import timedelta
from django.utils import timezone

from django.db import models
from django.conf import settings

import re
import overdrive.tasks
import bibliotheca.tasks
import connector.tasks
import hoopla.tasks

providers = {
    'overdrive': overdrive.tasks,
    'bibliotheca': bibliotheca.tasks,
    'hoopla': hoopla.tasks,
}


class WorkRecord(models.Model):

    title = models.CharField(max_length=1023, blank=True)
    author = models.CharField(max_length=1023, blank=True)
    primary_bib_record = models.ForeignKey(
        'BibliographicRecord',
        on_delete=models.SET_NULL,
        null=True)

    def __str__(self):
        return str(self.title)

    def get_popularity(self):
        dates = {
            'week': timezone.now() - timedelta(days=7),
            'month': timezone.now() - timedelta(days=30),
            'year': timezone.now() - timedelta(days=365),
        }
        popularities = {}
        for k, date in dates.items():
            popularity = Hold.objects.filter(
                bib_record__in=self.bib_records.all(),
                date_created__gt=date).count()
            popularities[k] = popularity
        popularities['all_time'] = Hold.objects.filter(
            bib_record__in=self.bib_records.all()).count()
        return popularities

    def update_primary_bib_record(self):
        self.primary_bib_record = max(
            self.bib_records.all(),
            key=lambda bib: bib.precedence)
        self.title = self.primary_bib_record.browse_title
        self.author = self.primary_bib_record.author
        self.save()


class ISBN(models.Model):

    isbn = models.CharField(max_length=15)

    def __str__(self):
        return str(self.isbn)


class BibliographicRecord(models.Model):

    ils_id = models.IntegerField(unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    work_record = models.ForeignKey(
        WorkRecord,
        on_delete=models.SET_NULL,
        related_name='bib_records',
        null=True)
    browse_author = models.CharField(max_length=1023, blank=True)
    author = models.CharField(max_length=1023, blank=True)
    browse_title = models.CharField(max_length=1023, blank=True)
    title = models.CharField(max_length=1023, blank=True)
    subtitle = models.CharField(max_length=1023, blank=True)
    part = models.CharField(max_length=1023, blank=True)
    part_num = models.CharField(max_length=1023, blank=True)
    isbns = models.ManyToManyField(ISBN, related_name='bib_records')
    provider = models.CharField(max_length=16, null=True)
    provider_id = models.CharField(max_length=64, blank=True)
    format_abbr = models.CharField(max_length=3, blank=True)
    abs_mat_code = models.CharField(max_length=32, blank=True)
    precedence = models.IntegerField()

    def __str__(self):
        return str(self.ils_id)

    @task
    def get_availability(self):
        resp = {"locum_id": self.ils_id}
        if self.provider in providers.keys():
            provider = providers[self.provider]
        else:
            provider = connector.tasks
        if self.provider_id:
            provider_id = self.provider_id
        else:
            provider_id = self.ils_id
        details = provider.get_availability(provider_id)
        resp.update(details)
        return resp

    def pull_bib_record(self):
        bib = connector.tasks.get_bib(self.ils_id)
        if bib:
            self.browse_title = bib.get('title_full', '')
            self.browse_author = bib.get('author_full', '')
            self.author = bib.get('author', '')
            self.title = bib.get('title', '')
            self.subtitle = bib.get('subtitle', '')
            self.part = bib.get('part', "")
            self.part_num = bib.get('part_num', "")
            self.provider = bib.get('provider', '')
            self.provider_id = bib.get('provider_id', '')
            self.precedence = bib.get('precedence', '')
            self.format_abbr = bib.get('format_abbr', '')
            self.abs_mat_code = bib.get('abs_mat_type')
            if self.abs_mat_code != 'other':
                self.save()
                self.assign_work_record()

    def assign_isbns(self, isbns=[]):
        if not isbns:
            bib = connector.tasks.get_bib(self.ils_id)
            if bib:
                isbns = bib['isbns']
            else:
                isbns = []
        for isbn in isbns:
            try:
                isbn_object = ISBN.objects.get(isbn=isbn)
            except ISBN.DoesNotExist:
                isbn_object = ISBN(isbn=isbn)
                isbn_object.save()
            self.isbns.add(isbn_object)

    def assign_work_record(self):
        bib = connector.tasks.get_bib(self.ils_id)
        if bib:
            work_note = bib.get('work_id')
            if work_note:
                if '>' in work_note:
                    old_work_id, key = work_note.split('>')
                    work_id = int(old_work_id)
                else:
                    work_id = int(work_note)
                if not self.work_record or self.work_record.id != work_id:
                    try:
                        work_record = WorkRecord.objects.get(id=work_id)
                    except WorkRecord.DoesNotExist:
                        work_record = WorkRecord(
                            id=work_id)
                    if not work_record.primary_bib_record or self.precedence > work_record.primary_bib_record.precedence:
                        work_record.primary_bib_record = self
                        work_record.title = self.browse_title
                        work_record.author = self.author
                        work_record.save()
                    self.work_record = work_record
                    self.save()
            elif self.work_record:
                assignment = {self.ils_id: self.work_record.id}
                connector.tasks.add_work_id_to_bib(assignment)

    def make_work_record(self):
        assignment = {}
        self = BibliographicRecord.objects.get(id=self.id)
        if self.work_record is None:
            relatives = self.get_validated_search_relatives()
            bib_records = [
                BibliographicRecord.objects.get(
                    ils_id=relative)
                for relative in relatives
            ]
            allegancies = set([
                bib_record.work_record.id
                for bib_record in bib_records
                if bib_record.work_record
            ])
            if len(allegancies) == 1:
                work_record = WorkRecord.objects.get(id=allegancies.pop())
            else:
                work_record = WorkRecord()
                work_record.save()
                if len(allegancies) > 1:
                    bib_records = [
                        bib_record
                        for bib_record in bib_records
                        if not bib_record.work_record]
            if bib_records:
                precedence = self.precedence
                precedent = self
                for bib_record in bib_records:
                    if bib_record.work_record is None:
                        bib_record.work_record = work_record
                        bib_record.save()
                        assignment.update({bib_record.ils_id: work_record.id})
                        if bib_record.precedence > precedence:
                            precedence = bib_record.precedence
                            precedent = bib_record
                work_record.primary_bib_record = precedent
                work_record.title = precedent.browse_title
                work_record.author = precedent.author
                work_record.save()
        return assignment

    def get_search_relatives(self):
        relatives = set([self.ils_id])
        if self.plays_well_with_others():
            es_index = 'locum'
            es = Elasticsearch('elasticsearch:9200')
            author_last_name = self.author.split(' ')[-1]
            body = {
                "query":
                {
                    "bool": {
                        "should": [
                            {"match": {
                                "title_full": {"query": self.browse_title}}}
                        ],
                        "must": [
                            {"match": {
                                "author": {"query": author_last_name}}}
                        ]
                    }
                },
                "size": 20
            }
            result = es.search(index=es_index, doc_type='bib', body=body)
            question_hits = [hit for hit in result['hits']['hits']
                             if hit['_source']['bnum'] == self.ils_id]
            if question_hits:
                question_hit = question_hits[0]
                base_score_index = question_hits.index(question_hit)
                scores = [hit['_score'] for hit in result['hits']['hits']]
                ils_ids = [hit['_source']['bnum'] for hit
                           in result['hits']['hits']]
                relatives = set(
                    ils_ids[:boundary_finder(base_score_index, scores) + 1]
                )
        return relatives

    def get_validated_search_relatives(self):
        relatives = self.get_search_relatives()
        validated_relatives = set({self.ils_id})
        for relative in relatives:
            if relative != self.ils_id:
                try:
                    rel_bib = BibliographicRecord.objects.get(ils_id=relative)
                    if self.ils_id in rel_bib.get_search_relatives():
                        validated_relatives.add(rel_bib.ils_id)
                except BibliographicRecord.DoesNotExist:
                    pass
        return validated_relatives

    def plays_well_with_others(self):
        return (bool(self.title)
                and bool(self.author)
                and not self.contains_fragmentation_indicators()
                and (self.format_abbr
                     in settings.CONNECTOR['polaris']['work_record_material_types']))

    def contains_fragmentation_indicators(self):
        fragmentation_exp = r'\b(?:vol(?:ume)?|issue|parte?|number)\b'
        numbers = r'\d+'
        years = r'\d{4}'
        parts = [self.subtitle, self.part, self.part_num]
        if [part for part in parts
                if re.search(fragmentation_exp, part.lower())
                or re.search(numbers, part.lower())
                and not re.search(years, part.lower())]:
            return True
        elif (re.search(fragmentation_exp, self.browse_title.lower())
                and re.search(numbers, self.browse_title.lower())):
            return True
        else:
            return False


def boundary_finder(base_score_index, scores):
    if len(scores) == 1:
        return 0
    sobel = [abs(scores[i] - scores[i + 1])
             for i in range(len(scores) - 1)]
    if sum(sobel) <= 0.0:
        return len(sobel)
    boundary_threshold = sobel.index(max(sobel))
    boundary = max(boundary_threshold, base_score_index)
    if len(scores) > 10 or scores[0] > 2 * scores[-1]:
        return boundary
    else:
        return len(scores)


class Hold(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    bib_record = models.ForeignKey(
        BibliographicRecord,
        related_name="holds")
