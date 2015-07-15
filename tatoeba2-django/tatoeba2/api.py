from tastypie import fields
from tastypie.resources import ModelResource, ALL
from tastypie.authorization import Authorization
from .api_base import BaseSearchResource, UCharField, IDPaginator
from .models import Sentences
from .search_indexes import (
    SentencesIndex, TagsIndex, SentencesListsIndex, SentenceCommentsIndex,
    WallIndex
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
        autoquery_fields = [
            'sentence_text', 'sentence_text_stemmed',
            'tags', 'lang', 'owner',
            'trans_langs', 'trans_owners'
            ]
        stem_fields = ['sentence_text_stemmed']
        allowed_methods = ['get']

filtering = {'django_id': SEARCH_FILTERS}

for f in SentencesSearchResource._meta.index.fields.keys():
    if f == 'text': continue
    filtering.update({f: SEARCH_FILTERS})

SentencesSearchResource._meta.filtering = filtering


class TagsSearchResource(BaseSearchResource):
    class Meta:
        resource_name = 'tags_search'
        index = TagsIndex()
        autoquery_fields = [
            'name', 'user'
            ]
        autocomplete_fields = ['name_ngram']
        allowed_methods = ['get']

filtering = {'django_id': SEARCH_FILTERS}

for f in TagsSearchResource._meta.index.fields.keys():
    if f == 'text': continue
    filtering.update({f: SEARCH_FILTERS})

TagsSearchResource._meta.filtering = filtering


class SentencesListsSearchResource(BaseSearchResource):
    class Meta:
        resource_name = 'sentences_lists_search'
        index = SentencesListsIndex()
        autoquery_fields = [
            'name', 'user'
            ]
        autocomplete_fields = ['name_ngram']
        allowed_methods = ['get']

filtering = {'django_id': SEARCH_FILTERS}

for f in SentencesListsSearchResource._meta.index.fields.keys():
    if f == 'text': continue
    filtering.update({f: SEARCH_FILTERS})

SentencesListsSearchResource._meta.filtering = filtering


class SentenceCommentsSearchResource(BaseSearchResource):
    class Meta:
        resource_name = 'sentence_comments_search'
        index = SentenceCommentsIndex()
        autoquery_fields = [
            'comment_text', 'user'
            ]
        allowed_methods = ['get']

filtering = {'django_id': SEARCH_FILTERS}

for f in SentenceCommentsSearchResource._meta.index.fields.keys():
    if f == 'text': continue
    filtering.update({f: SEARCH_FILTERS})

SentenceCommentsSearchResource._meta.filtering = filtering


class WallSearchResource(BaseSearchResource):
    class Meta:
        resource_name = 'wall_search'
        index = WallIndex()
        autoquery_fields = [
            'content', 'owner'
            ]
        allowed_methods = ['get']

filtering = {'django_id': SEARCH_FILTERS}

for f in WallSearchResource._meta.index.fields.keys():
    if f == 'text': continue
    filtering.update({f: SEARCH_FILTERS})

WallSearchResource._meta.filtering = filtering
