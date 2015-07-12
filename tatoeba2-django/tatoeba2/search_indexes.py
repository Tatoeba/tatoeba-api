from haystack import indexes
from datetime import datetime
from .utils import now, stemmer
from .models import (
    Sentences,
    )


class SentencesIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    id = indexes.IntegerField(model_attr='id')
    sentence_text = indexes.CharField(model_attr='text')
    sentence_text_stemmed = indexes.CharField()
    lang = indexes.CharField(model_attr='lang', default='und')
    user_id = indexes.IntegerField(model_attr='user_id', default=0)
    created = indexes.DateTimeField(model_attr='created', default=datetime(1,1,1))
    modified = indexes.DateTimeField(model_attr='modified', default=datetime(1,1,1))
    hasaudio = indexes.CharField(model_attr='hasaudio', default='no')
    lang_id = indexes.IntegerField(model_attr='lang_id')
    correctness = indexes.IntegerField(model_attr='correctness')

    def get_model(self):
        return Sentences

    def get_updated_field(self):
        return 'modified'

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare(self, object):
        self.prepared_data = super(SentencesIndex, self).prepare(object)

        text = object.text.decode('utf-8', 'ignore')
        lang = object.lang

        self.prepared_data['sentence_text'] = text
        self.prepared_data['sentence_text_stemmed'] = stemmer.stem(text, lang)

        return self.prepared_data
