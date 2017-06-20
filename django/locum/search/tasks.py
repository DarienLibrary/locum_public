from elasticsearch import Elasticsearch
from django.conf import settings

from harvest.models import WorkRecord
from harvest.serializers import WorkSerializer


es_uri = settings.ELASTIC['uri']
es_index = settings.ELASTIC['bib_index']
es_work_index = settings.ELASTIC['work_index']
es = Elasticsearch([es_uri])


def search(query, limit, offset, search_type, popularity_period, popularity_weight, facets=[], sort=[]):

    fields = {
        'keyword': [
            "title^3",
            "title.stemmed^3",
            "author_full^2",
            "subject",
            "contributors"],
        'title': [
            "title",
            "title.stemmed"],
        'author': [
            "author_full",
            "contributors"],
        'subject': ["subject"],
        'callnum': ["call_num"],
        # 'tags': None,
    }

    if query == "*":
        q = {"match_all": {}}
    else:
        q = {
            "multi_match": {
                "query": query,
                "fields": fields[search_type]
            }
        }

    # filters = [{"term": {"suppress": False}}]
    filters = []
    filters += facets

    sort.append('_score')

    f = {
        "bool": {
            "must": filters
        }
    }

    body = {
        "query": {
            "function_score": {
                "query": {
                    "filtered": {
                        "query": q,
                        "filter": f,
                    }
                },
                "field_value_factor": {
                    "field": popularity_period,
                    "modifier": "log2p",
                    "factor": popularity_weight
                }
            }
        },
        "size": limit,
        "from": offset,
        "aggs": {
            "abs_mat_codes": {
                "terms": {
                    "field": "abs_mat_codes",
                    "size": 0,
                }
            },
            "age": {
                "terms": {
                    "field": "age"
                }
            },
            "pub_year": {
                "stats": {
                    "field": "pub_year"
                }
            }
        },
        "sort": sort
    }
    result = es.search(index=es_work_index, doc_type='work', body=body)
    total = result['hits']['total']
    aggregations = result['aggregations']
    work_id = [hit['_source']['work_id'] for hit in result['hits']['hits']]
    resp = search_presentation(work_id)
    resp.update({
        'total': total,
        'aggregations': aggregations,
    })
    return resp


def search_presentation(work_ids):
    resp = {
        "success": True,
        "works": [],
    }
    for work_id in work_ids:
        try:
            work_record = WorkRecord.objects.get(id=work_id)
        except WorkRecord.DoesNotExist:
            work_record = None
        if work_record:
            work = WorkSerializer(instance=work_record).data
            resp['works'].append(work)
    return resp
