from django.conf.urls import patterns, include, url
from tastypie.api import Api
from .api import (
    SentencesResource, SentencesSearchResource, TagsSearchResource,
    SentencesListsSearchResource, SentenceCommentsSearchResource,
    WallSearchResource
    )


api = Api(api_name='0.1')
api.register(SentencesResource())
api.register(SentencesSearchResource())
api.register(TagsSearchResource())
api.register(SentencesListsSearchResource())
api.register(SentenceCommentsSearchResource())
api.register(WallSearchResource())

urlpatterns = patterns('',
    url(r'^', include(api.urls)),
)
