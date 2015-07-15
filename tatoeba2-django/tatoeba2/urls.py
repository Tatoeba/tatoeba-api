from django.conf.urls import patterns, include, url
from tastypie.api import Api
from .api import (
    SentencesResource, SentencesSearchResource, TagsSearchResource
    )


api = Api(api_name='0.1')
api.register(SentencesResource())
api.register(SentencesSearchResource())
api.register(TagsSearchResource())

urlpatterns = patterns('',
    url(r'^', include(api.urls)),
)
