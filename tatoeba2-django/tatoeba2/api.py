from tastypie import fields
from tastypie.resources import ModelResource, ALL
from tastypie.authorization import Authorization
from .api_base import BaseSearchResource, UCharField, IDPaginator
from .models import Sentences
from .search_indexes import (
    SentencesIndex,
    )
from datetime import datetime


SEARCH_FILTERS = [
        'contains', 'range', 'in', 'exact', 'startswith',
        'gt', 'gte', 'lt', 'lte'
        ]


class SentencesResource(ModelResource):
    created = fields.DateTimeField(attribute='created', default=datetime(1, 1, 1))
    modified = fields.DateTimeField(attribute='modified', default=datetime(1, 1, 1))
    text = UCharField(attribute='text')

    class Meta:
        queryset = Sentences.objects.all()
        allowed_methods = ['get']
        authorization = Authorization()
        paginator_class = IDPaginator
        max_limit = 100

filtering = {}

for f in SentencesResource._meta.object_class._meta.fields:
    filtering.update({f.name: ALL})

SentencesResource._meta.filtering = filtering


class SentencesSearchResource(BaseSearchResource):
    class Meta:
        resource_name = 'sentences_search'
        index = SentencesIndex()
        autoquery_fields = ['sentence_text', 'sentence_text_stemmed']
        stem_fields = ['sentence_text_stemmed']
        allowed_methods = ['get']

filtering = {'django_id': SEARCH_FILTERS}

for f in SentencesSearchResource._meta.index.fields.keys():
    if f == 'text': continue
    filtering.update({f: SEARCH_FILTERS})

SentencesSearchResource._meta.filtering = filtering
