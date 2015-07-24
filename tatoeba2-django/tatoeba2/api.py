from tastypie import fields
from tastypie.resources import ModelResource, ALL
from tastypie.authorization import Authorization
from .api_base import BaseSearchResource, UCharField, IDPaginator
from .models import (
    Sentences, Tags, TagsSentences, Users
    )
from .search_indexes import (
    SentencesIndex, TagsIndex, SentencesListsIndex, SentenceCommentsIndex,
    WallIndex, UsersIndex
    )
from datetime import datetime


SEARCH_FILTERS = [
        'contains', 'range', 'in', 'exact', 'startswith',
        'gt', 'gte', 'lt', 'lte'
        ]

FILTERS = ['exact', 'in']
FILTERS_NUM = FILTERS + ['lt', 'lte', 'gt', 'gte', 'range']
FILTERS_DATE = FILTERS_NUM + ['year', 'month', 'day', 'hour', 'minute']

def set_filters(resource, exclude=[]):
    filtering = {}

    for f in resource._meta.object_class._meta.fields:
        if f.name in exclude:
            continue

        ftype = type(f).__name__

        if ftype == 'CharField':
            filtering.update({f.name: FILTERS})
        elif ftype in ('AutoField', 'IntegerField'):
            filtering.update({f.name: FILTERS_NUM})
        elif ftype in ('DateTimeField', 'DateField'):
            filtering.update({f.name: FILTERS_DATE})

    resource._meta.filtering = filtering

def set_search_filters(resource, exclude=[]):
    exclude += ['text']
    filtering = {}
    filtering.update({'django_id': SEARCH_FILTERS})

    for f in resource._meta.index.fields.keys():
        if f in exclude:
            continue
        filtering.update({f: SEARCH_FILTERS})

    resource._meta.filtering = filtering


class SentencesResource(ModelResource):
    created = fields.DateTimeField(attribute='created', default=datetime(1, 1, 1))
    modified = fields.DateTimeField(attribute='modified', default=datetime(1, 1, 1))
    text = UCharField(attribute='text')

    class Meta:
        queryset = Sentences.objects.all()
        allowed_methods = ['get']
        excludes = ['dico_id']
        authorization = Authorization()
        paginator_class = IDPaginator
        max_limit = 100

set_filters(SentencesResource, exclude=['text'])


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

set_search_filters(SentencesSearchResource)


class TagsResource(ModelResource):
    created = fields.DateTimeField(attribute='created', default=datetime(1, 1, 1))
    description = UCharField(attribute='description', default='')

    class Meta:
        queryset = Tags.objects.all()
        excludes = ['internal_name']
        allowed_methods = ['get']
        authorization = Authorization()
        paginator_class = IDPaginator
        max_limit = 100

set_filters(TagsResource, exclude=['name', 'description'])


class TagsSentencesResource(ModelResource):
    added_time = fields.DateTimeField(attribute='added_time', default=datetime(1, 1, 1))
    sentence = fields.ForeignKey('tatoeba2.api.SentencesResource', attribute='sentence')
    user = fields.ForeignKey('tatoeba2.api.UsersResource', attribute='user')

    class Meta:
        queryset = TagsSentences.objects.all()
        resource_name = 'tags_sentences'
        excludes = []
        allowed_methods = ['get']
        authorization = Authorization()
        paginator_class = IDPaginator
        max_limit = 100

set_filters(TagsSentencesResource, exclude=['name', 'description'])


class TagsSearchResource(BaseSearchResource):
    class Meta:
        resource_name = 'tags_search'
        index = TagsIndex()
        autoquery_fields = [
            'name', 'user'
            ]
        autocomplete_fields = ['name_ngram']
        allowed_methods = ['get']

set_search_filters(TagsSearchResource)


class SentencesListsSearchResource(BaseSearchResource):
    class Meta:
        resource_name = 'sentences_lists_search'
        index = SentencesListsIndex()
        autoquery_fields = [
            'name', 'user'
            ]
        autocomplete_fields = ['name_ngram']
        allowed_methods = ['get']

set_search_filters(SentencesListsSearchResource)


class SentenceCommentsSearchResource(BaseSearchResource):
    class Meta:
        resource_name = 'sentence_comments_search'
        index = SentenceCommentsIndex()
        autoquery_fields = [
            'comment_text', 'user'
            ]
        allowed_methods = ['get']

set_search_filters(SentenceCommentsSearchResource)


class WallSearchResource(BaseSearchResource):
    class Meta:
        resource_name = 'wall_search'
        index = WallIndex()
        autoquery_fields = [
            'content', 'owner'
            ]
        allowed_methods = ['get']

set_search_filters(WallSearchResource)


class UsersResource(ModelResource):
    since = fields.DateTimeField(attribute='since', default=datetime(1, 1, 1))
    birthday = fields.DateTimeField(attribute='since', default=datetime(1, 1, 1))

    class Meta:
        queryset = Users.objects.all()
        excludes = ['password', 'email']
        allowed_methods = ['get']
        authorization = Authorization()
        paginator_class = IDPaginator
        max_limit = 100

set_filters(UsersResource, exclude=[
            'name', 'description', 'settings', 'homepage', 'image'
            ])


class UsersSearchResource(BaseSearchResource):
    class Meta:
        resource_name = 'users_search'
        index = UsersIndex()
        autoquery_fields = []
        allowed_methods = ['get']

set_search_filters(UsersSearchResource)
