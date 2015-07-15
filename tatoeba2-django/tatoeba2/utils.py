from pytz import UTC as utc
from datetime import datetime
from django.conf import settings


def now():
    return datetime.utcnow().replace(tzinfo=utc)

def uclean(string):
    return string.decode('utf-8', 'ignore')

STEMMERS = getattr(settings, 'HAYSTACK_STEMMERS')

TOKENIZERS = getattr(settings, 'HAYSTACK_TOKENIZERS', {})

STOP_WORDS = getattr(settings, 'HAYSTACK_STOP_WORDS', {})


class Stemmer(object):

    def __init__(self, lang=None):
        self.lang = lang
        self.stemmer = STEMMERS.get(lang, None)
        self.tokenizer = TOKENIZERS.get(lang, None)
        self.stop_words = set(STOP_WORDS.get(lang, set()))

    def stem(self, text, lang):
        lang = lang or self.lang
        stemmer = STEMMERS.get(lang, None) or self.stemmer

        if not stemmer:
            return ''

        stemmed_text = []

        for token in self.tokenize(text):
            if token not in self.stop_words:
                token = stemmer.stem(token)
                stemmed_text.append(token)

        stemmed_text = ' '.join(stemmed_text)

        return stemmed_text

    def tokenize(self, text):
        tokenizer = self.tokenizer if self.tokenizer else lambda s: s.split()

        for token in tokenizer(text):
            yield token

stemmer = Stemmer()
