from haystack import indexes
from datetime import datetime
from .utils import now, stemmer, uclean, limit_string
from .models import (
    Sentences, Users, SentencesTranslations, UsersLanguages, Tags,
    TagsSentences, SentencesLists, SentenceComments, Wall, Groups
    )
from collections import defaultdict


class LimCharField(indexes.CharField):
    def convert(self, value):
        if value is None:
            return None

        return limit_string(value)


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

            if None in props['lang']:
                props['lang'].remove(None)
                props['lang'].add('und')
            if '' in props['lang']:
                props['lang'].remove('')
                props['lang'].add('und')

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


class SentenceCommentsIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    id = indexes.IntegerField(model_attr='id')
    sentence_id = indexes.IntegerField(model_attr='sentence_id')
    comment_text = LimCharField(model_attr='text', default='')
    user = indexes.CharField(default='')
    created = indexes.DateTimeField(model_attr='created', default=datetime(1,1,1))
    modified = indexes.DateTimeField(model_attr='modified', default=datetime(1,1,1))
    hidden = indexes.IntegerField(model_attr='hidden')

    def get_model(self):
        return SentenceComments

    def get_updated_field(self):
        return 'modified'

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare(self, object):
        self.prepared_data = super(SentenceCommentsIndex, self).prepare(object)

        user = Users.objects.filter(id=object.user_id)
        user = user[0] if user else ''

        self.prepared_data['user'] = user

        return self.prepared_data


class WallIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    id = indexes.IntegerField(model_attr='id')
    owner = indexes.CharField(default='')
    parent_id = indexes.IntegerField(model_attr='parent_id', default=0)
    date = indexes.DateTimeField(model_attr='modified', default=datetime(1,1,1))
    title = indexes.CharField(model_attr='title', default='')
    content = LimCharField(model_attr='content', default='')
    lft = indexes.IntegerField(model_attr='lft', default=0)
    rght = indexes.IntegerField(model_attr='rght', default=0)
    modified = indexes.DateTimeField(model_attr='modified', default=datetime(1,1,1))

    def get_model(self):
        return Wall

    def get_updated_field(self):
        return 'modified'

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare(self, object):
        self.prepared_data = super(WallIndex, self).prepare(object)

        user = Users.objects.filter(id=object.owner)
        owner = user[0] if user else ''

        self.prepared_data['owner'] = owner

        return self.prepared_data


class UsersIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    id = indexes.IntegerField(model_attr='id')
    username = indexes.CharField(model_attr='username')
    since = indexes.DateTimeField(model_attr='since', default=datetime(1,1,1))
    last_time_active = indexes.DateTimeField(default=datetime(1,1,1))
    level = indexes.IntegerField(model_attr='level')
    group = indexes.CharField()
    send_notifications = indexes.BooleanField()
    name = indexes.CharField(model_attr='name')
    birthday = indexes.DateTimeField(model_attr='birthday', default=datetime(1,1,1))
    description = LimCharField(model_attr='description')
    homepage = indexes.CharField(model_attr='homepage')
    image = indexes.CharField(model_attr='image')
    country_id = indexes.CharField(model_attr='country_id', default='')
    settings = indexes.CharField(model_attr='settings')

    def get_model(self):
        return Users

    def get_updated_field(self):
        return 'since'

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare(self, object):
        self.prepared_data = super(UsersIndex, self).prepare(object)

        group = Groups.objects.get(id=object.group_id).name
        send_notifications = bool(object.send_notifications)
        last_time_active = datetime.fromtimestamp(object.last_time_active)

        self.prepared_data['group'] = group
        self.prepared_data['send_notifications'] = send_notifications
        self.prepared_data['last_time_active'] = last_time_active

        return self.prepared_data
