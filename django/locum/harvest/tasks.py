from celery import shared_task, chord
from celery.utils.log import get_task_logger
from elasticsearch import Elasticsearch, helpers
from elasticsearch.client import IndicesClient
from datetime import datetime
import json
from django.conf import settings

import connector.tasks
from .models import BibliographicRecord, WorkRecord

es_uri = settings.ELASTIC['uri']
es_index = settings.ELASTIC['bib_index']
es_work_index = settings.ELASTIC['work_index']

logger = get_task_logger(__name__)


def get_provider_details(ils_id):
    try:
        bib_record = BibliographicRecord.objects.get(ils_id=ils_id)
        return {
            "provider": bib_record.provider,
            "provider_id": bib_record.get_provider_id
        }
    except BibliographicRecord.DoesNotExist:
        return None


def get_ils_details(provider, provider_id):
    bib_records = BibliographicRecord.objects.filter(
        provider=provider,
        provider_id=provider_id)
    if bib_records:
        bib_record = bib_records[0]
        return {
            "found_bib": True,
            "title": bib_record.browse_title,
            "author": bib_record.author,
            "locum_id": bib_record.id,
            "provider_id": provider_id,
            "ils_id": bib_record.ils_id,
            "provider": provider,
            "format_abbr": bib_record.format_abbr,
            "abs_mat_code": bib_record.abs_mat_code,
        }
    else:
        return {
            "found_bib": False,
            "provider_id": provider_id,
            "provider": provider,
        }


def get_ils_details_for_item_id(item_id):
    ils_id = connector.tasks.get_bib_record_id_for_item(item_id)
    try:
        bib_record = BibliographicRecord.objects.get(ils_id=ils_id)
    except BibliographicRecord.DoesNotExist:
        bib_record = None
    if bib_record:
        return {
            "found_bib": True,
            "title": bib_record.browse_title,
            "author": bib_record.author,
            "locum_id": bib_record.id,
            "ils_id": bib_record.ils_id,
            "format_abbr": bib_record.format_abbr,
            "abs_mat_code": bib_record.abs_mat_code,
        }
    else:
        return {
            "found_bib": False,
        }


def get_patron_circulation(barcode):
    resp = connector.tasks.get_patron_circulation(barcode)
    for i in ['holds', 'checkouts']:
        for item in resp[i]:
            try:
                bib_record = BibliographicRecord.objects.get(
                    ils_id=item['ils_id'])
            except BibliographicRecord.DoesNotExist:
                bib_record = None
            if bib_record:
                item.update({
                    'locum_id': bib_record.id,
                    'abs_mat_code': bib_record.abs_mat_code,
                    'format_abbr': bib_record.format_abbr,
                })
            else:
                bib = connector.tasks.get_bib(item['ils_id'])
                if bib:
                    item.update({
                        'locum_id': None,
                        'abs_mat_code': bib['abs_mat_code'],
                        'format_abbr': bib['format_abbr'],
                    })
                else:
                    item.update({
                        'locum_id': None,
                        'abs_mat_code': None,
                        'format_abbr': None,
                    })

    return resp


def patron_renew_all_items(barcode):
    resp = connector.tasks.patron_renew_all_items(barcode)
    for item in resp['items']:
        item_id = item['item_id']
        details = get_ils_details_for_item_id(item_id)
        item.update(details)
    return resp


def patron_renew_items(barcode, items):
    resp = connector.tasks.patron_renew_items(barcode, items)
    for item in resp['items']:
        item_id = item['item_id']
        details = get_ils_details_for_item_id(item_id)
        item.update(details)
    return resp


def get_works():
    work_is_alive = False
    fields = [
        'author_full',
        'title',
        'subject',
        'pub_year',
        'age',
        'call_num',
    ]
    valid_ils_ids = set(connector.tasks.get_bib_record_ids())
    bib_ids = WorkRecord.objects.values_list(
        'primary_bib_record__ils_id',
        flat=True)
    for bib in connector.tasks.get_bibs(bib_ids):
        if bib:
            bib_record = BibliographicRecord.objects.get(ils_id=bib['bnum'])
            work_record = bib_record.work_record
            if work_record:
                work = {}
                for field in fields:
                    work[field] = bib.get(field, '')
                work['work_id'] = work_record.id

                abs_mat_codes = []
                contributors = []
                for bib_record in work_record.bib_records.all():
                    if bib_record.ils_id in valid_ils_ids:
                        work_is_alive = True
                        bib_details = connector.tasks.get_bib(bib_record.ils_id)
                        abs_mat_code = bib_record.abs_mat_code
                        if abs_mat_code not in abs_mat_codes:
                            abs_mat_codes.append(abs_mat_code)
                        if bib_details:
                            if bib_details['bookgroup'] and 'bookgroup' not in abs_mat_codes:
                                abs_mat_codes.append('bookgroup')
                            for contributor in bib_details['contributors']:
                                if contributor not in contributors:
                                    contributors.append(contributor)
                work['contributors'] = contributors
                work['abs_mat_codes'] = abs_mat_codes
                work.update(work_record.get_popularity())
                if work_is_alive:
                    yield work


def get_es_index_actions(index):
    '''
    Generates Elasticsearch indexing actions for each bib in ILS
    for consumption by elasticsearch.helpers.streaming_bulk
    '''
    fields = [
        'title_full',
        'author',
        'bnum',
    ]

    for bib in connector.tasks.get_bibs():
        if bib:
            reduced_bib = {}
            for field in fields:
                reduced_bib[field] = bib.get(field, '')
            try:
                bib_record = BibliographicRecord.objects.get(ils_id=(bib['bnum']))
            except BibliographicRecord.DoesNotExist:
                bib_record = None
            if bib_record:
                yield {'_index': index,
                       '_type': 'bib',
                       '_id': bib_record.ils_id,
                       '_source': reduced_bib
                       }


@shared_task
def populate_es_works():
    es = Elasticsearch([es_uri])
    ic = IndicesClient(es)
    real_index_name = '{}_{}'.format(
        es_work_index, int(datetime.timestamp(datetime.now())))
    with open("es_config.json") as f:
        body = json.loads(f.read())
        es.indices.create(real_index_name, body=body)
    actions = iter(get_es_index_work_actions(real_index_name))
    for result in helpers.streaming_bulk(es, actions):
        pass
    old_indices = [
        k for k, v in ic.get_aliases().items()
        if es_work_index in v['aliases'].keys()]
    ic.put_alias(index=real_index_name, name=es_work_index)
    for index in old_indices:
        es.indices.delete(index)
        logger.info('Previous Index Deleted: {}'.format(index))


def get_es_index_work_actions(index):
    '''
    Generates Elasticsearch indexing actions for each work in harvest
    for consumption by elasticsearch.helpers.streaming_bulk
    '''
    for work in get_works():
        yield {'_index': index,
               '_type': 'work',
               '_id': work['work_id'],
               '_source': work
               }


@shared_task
def full_import():
    import_new_bib_records()
    make_manual_edits()
    update_outdated_bibs()
    populate_es()
    give_work_to_workless()
    populate_es_works()


@shared_task
def import_new_bib_records():
    make_bib_id_changes()
    live_bib_ids = set(connector.tasks.get_bib_record_ids())
    recorded_bib_ids = set(
        BibliographicRecord.objects.all().values_list('ils_id', flat=True))
    unrecorded_bib_ids = live_bib_ids - recorded_bib_ids
    create_bib_records(unrecorded_bib_ids)
    dead_bib_ids = recorded_bib_ids - live_bib_ids
    BibliographicRecord.objects.filter(ils_id__in=dead_bib_ids).delete()
    WorkRecord.objects.filter(bib_records=None).delete()
    works_without_primary_bib = WorkRecord.objects.filter(primary_bib_record=None)
    for work in works_without_primary_bib:
        work.update_primary_bib_record()


@shared_task
def make_bib_id_changes():
    recorded_bib_ids = BibliographicRecord.objects.all().values_list(
        'ils_id',
        flat=True)
    id_changes = connector.tasks.get_bib_id_changes()
    for old in recorded_bib_ids:
        new = id_changes.get(old)
        if new:
            old_bib_record = BibliographicRecord.objects.get(ils_id=old)
            try:
                new_bib_record = BibliographicRecord.objects.get(ils_id=new)
            except BibliographicRecord.DoesNotExist:
                old_bib_record.ils_id = new
                old_bib_record.save()


def create_bib_records(bib_ids=[]):
    for bib_id in bib_ids:
        try:
            bib_record = BibliographicRecord.objects.get(ils_id=bib_id)
        except BibliographicRecord.DoesNotExist:
            bib_record = BibliographicRecord(ils_id=bib_id)
            bib_record.pull_bib_record()


def update_outdated_bibs():
    edit_dates = connector.tasks.get_changes()
    for bib_id, date_updated in edit_dates.items():
        try:
            bib_record = BibliographicRecord.objects.get(ils_id=bib_id)
        except BibliographicRecord.DoesNotExist:
            bib_record = None
        if bib_record and bib_record.date_updated < date_updated:
            bib_record.pull_bib_record()


def make_manual_edits():
    assignment = {}
    work_notes = connector.tasks.get_manual_notes()
    for key, bib_ids in work_notes.items():
        work_record = WorkRecord()
        work_record.save()
        for bib_id in bib_ids:
            try:
                bib_record = BibliographicRecord.objects.get(ils_id=bib_id)
            except BibliographicRecord.DoesNotExist:
                bib_record = None
            if bib_record:
                old_work_record = bib_record.work_record
                bib_record.work_record = work_record
                bib_record.save()
                if (not work_record.primary_bib_record or
                        bib_record.precedence > work_record.primary_bib_record.precedence):
                    work_record.title = bib_record.browse_title
                    work_record.author = bib_record.author
                    work_record.primary_bib_record = bib_record
                    work_record.save()
                assignment.update({bib_id: work_record.id})
                if old_work_record:
                    if len(old_work_record.bib_records.all()) == 0:
                        old_work_record.delete()
                    elif old_work_record.primary_bib_record is None:
                        old_work_record.update_primary_bib_record()
        if len(work_record.bib_records.all()) == 0:
            work_record.delete()
    connector.tasks.add_work_id_to_bib(assignment)


@shared_task
def populate_es():
    '''
    Builds new index, populates that index from ILS, when
    finished, creates an alias to the production alias, and
    removes previous aliases.
    '''
    es = Elasticsearch([es_uri])
    ic = IndicesClient(es)
    real_index_name = '{}_{}'.format(
        es_index, int(datetime.timestamp(datetime.now())))
    with open("es_config.json") as f:
        body = json.loads(f.read())
        es.indices.create(real_index_name, body=body)
    actions = iter(get_es_index_actions(real_index_name))
    logger.info('Populating Index: {}'.format(real_index_name))
    for result in helpers.streaming_bulk(es, actions):
        pass
    logger.info('Index Populated: {}'.format(real_index_name))
    old_indices = [
        k for k, v in ic.get_aliases().items()
        if es_index in v['aliases'].keys()]
    ic.put_alias(index=real_index_name, name=es_index)
    for index in old_indices:
        es.indices.delete(index)


def give_work_to_workless():
    for bib in BibliographicRecord.objects.filter(work_record=None):
        assignment = bib.make_work_record()
        connector.tasks.add_work_id_to_bib(assignment)
