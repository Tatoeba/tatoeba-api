from django.conf.urls import patterns, include, url
from tastypie.api import Api
from .api import (
    SentencesResource, SentencesSearchResource
    )


api = Api(api_name='api')
api.register(SentencesResource())
api.register(SentencesSearchResource())

urlpatterns = patterns('',
    url(r'^', include(api.urls)),
)
