from haystack import indexes
from datetime import datetime
from .utils import now, stemmer, uclean
from .models import (
    Sentences, Users, SentencesTranslations, UsersLanguages, Tags,
    TagsSentences, SentencesLists
    )
from collections import defaultdict


class SentencesIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    id = indexes.IntegerField(model_attr='id')
    sentence_text = indexes.CharField()
    sentence_text_stemmed = indexes.CharField()
    lang = indexes.CharField(default='und')
    owner = indexes.CharField(default='')
    owner_is_native = indexes.BooleanField(default=False)
    is_orphan = indexes.BooleanField(default=True)
    tags = indexes.CharField(default='')
    is_tagged = indexes.BooleanField(default=False)
    created = indexes.DateTimeField(model_attr='created', default=datetime(1,1,1))
    modified = indexes.DateTimeField(model_attr='modified', default=datetime(1,1,1))
    has_audio = indexes.BooleanField(default=False)
    is_unapproved = indexes.BooleanField(default=False)
    trans_langs = indexes.CharField(default='')
    trans_owners = indexes.CharField(default='')
    trans_has_orphan = indexes.BooleanField(default=False)
    trans_has_audio = indexes.BooleanField(default=False)
    trans_is_unapproved = indexes.BooleanField(default=False)

    def get_model(self):
        return Sentences

    def get_updated_field(self):
        return 'modified'

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare(self, object):
        self.prepared_data = super(SentencesIndex, self).prepare(object)

        text = uclean(object.text)
        lang = object.lang
        user = Users.objects.filter(id=object.user_id)
        user = user[0] if user else None
        owner = user.username if user else ''
        owner = uclean(owner)
        is_orphan = not bool(owner)
        owner_is_native = bool(
            UsersLanguages.objects.filter(
                of_user_id=object.user_id, by_user_id=object.user_id,
                language_code=lang, level=5
                ).values_list('language_code', flat=True)
            )
        tags = Tags.objects.filter(
                    id__in=TagsSentences.objects\
                               .filter(sentence_id=object.id)\
                               .values_list('tag_id', flat=True)\
                    ).values_list('name', flat=True)
        tags = list(set(tags))
        tags = ' | '.join(tags) if tags else ''
        tags = uclean(tags)
        is_tagged = bool(tags)
        is_unapproved = bool(object.correctness == -1)
        has_audio = bool(object.hasaudio == 'shtooka' or object.hasaudio == 'from_users')

        direct_props = list(Sentences.objects.raw("""
                        SELECT `s`.`id`, `s`.`user_id`, `s`.`lang`, `s`.`correctness`, `s`.`hasaudio`
                        FROM `sentences` as `s`
                        JOIN `sentences_translations` as `t`
                        ON `t`.`translation_id` = `s`.id
                        WHERE `t`.`sentence_id` = %s ;
                        """, [object.id]))
        if direct_props:
            props = defaultdict(set)
            for prop in direct_props:
                for key in ('user_id', 'lang', 'correctness', 'hasaudio'):
                    props[key].add(getattr(prop, key))

            trans_langs = ' | '.join(list(props['lang']))
            trans_is_unapproved = -1 in props['correctness']
            trans_has_orphan = None in props['user_id']
            if trans_has_orphan: props['user_id'].remove(None)
            users = list(props['user_id'])
            users = Users.objects.filter(id__in=users).values_list('username', flat=True)
            trans_owners = ' | '.join(users)
            trans_has_audio = 'shtooka' in props['hasaudio'] or \
                              'from_users' in props['hasaudio']

            self.prepared_data['trans_langs'] = trans_langs
            self.prepared_data['trans_owners'] = trans_owners
            self.prepared_data['trans_has_audio'] = trans_has_audio
            self.prepared_data['trans_is_unapproved'] = trans_is_unapproved
            self.prepared_data['trans_has_orphan'] = trans_has_orphan

        self.prepared_data['sentence_text'] = text
        self.prepared_data['sentence_text_stemmed'] = stemmer.stem(text, lang)
        self.prepared_data['owner'] = owner
        self.prepared_data['is_orphan'] = is_orphan
        self.prepared_data['owner_is_native'] = owner_is_native
        self.prepared_data['tags'] = tags
        self.prepared_data['is_tagged'] = is_tagged
        self.prepared_data['is_unapproved'] = is_unapproved
        self.prepared_data['has_audio'] = has_audio

        return self.prepared_data


class TagsIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    id = indexes.IntegerField(model_attr='id')
    name = indexes.CharField(default='')
    name_ngram = indexes.EdgeNgramField(default='')
    description = indexes.CharField(default='')
    user = indexes.CharField(default='')
    created = indexes.DateTimeField(model_attr='created', default=datetime(1,1,1))

    def get_model(self):
        return Tags

    def get_updated_field(self):
        return 'created'

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare(self, object):
        self.prepared_data = super(TagsIndex, self).prepare(object)

        name = uclean(object.name)
        description = uclean(object.description) if object.description else ''
        user = Users.objects.filter(id=object.user_id)
        user = user[0] if user else ''

        self.prepared_data['name'] = name
        self.prepared_data['name_ngram'] = name
        self.prepared_data['user'] = user

        return self.prepared_data


class SentencesListsIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    id = indexes.IntegerField(model_attr='id')
    name = indexes.CharField(default='')
    name_ngram = indexes.EdgeNgramField(default='')
    user = indexes.CharField(default='')
    is_public = indexes.BooleanField()
    modified = indexes.DateTimeField(model_attr='modified', default=datetime(1,1,1))
    created = indexes.DateTimeField(model_attr='created', default=datetime(1,1,1))

    def get_model(self):
        return SentencesLists

    def get_updated_field(self):
        return 'modified'

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare(self, object):
        self.prepared_data = super(SentencesListsIndex, self).prepare(object)

        name = uclean(object.name)
        user = Users.objects.filter(id=object.user_id)
        user = user[0] if user else ''
        is_public = bool(object.is_public)

        self.prepared_data['name'] = name
        self.prepared_data['name_ngram'] = name
        self.prepared_data['user'] = user
        self.prepared_data['is_public'] = is_public

        return self.prepared_data
