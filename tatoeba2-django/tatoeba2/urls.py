from django.conf.urls import patterns, include, url
from tastypie.api import Api
from .api import (
    SentencesResource, SentencesSearchResource, TagsResource, TagsSearchResource,
    TagsSentencesResource, SentencesListsSearchResource, SentenceCommentsSearchResource,
    WallSearchResource, UsersResource, UsersSearchResource
    )


api = Api(api_name='0.1')
api.register(SentencesResource())
api.register(SentencesSearchResource())
api.register(TagsResource())
api.register(TagsSearchResource())
api.register(TagsSentencesResource())
api.register(SentencesListsSearchResource())
api.register(SentenceCommentsSearchResource())
api.register(WallSearchResource())
api.register(UsersResource())
api.register(UsersSearchResource())

urlpatterns = patterns('',
    url(r'^', include(api.urls)),
)
