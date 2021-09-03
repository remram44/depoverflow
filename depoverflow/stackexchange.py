import re

from .base import Item, InvalidReference


SITES = {
    r'stackoverflow\.com',
    r'superuser\.com',
    r'askubuntu\.com',
    r'serverfault\.com',
    r'[a-z0-9-]+\.stackexchange\.com',
}


re_question = re.compile(
    (
        r'^https?://({site})'
        r'/(?:questions|q)/([0-9]+)'
        r'(?:/(?:[^/]+(?:/[0-9]*)?)?)?$'
    ).format(site='|'.join('(?:{0})'.format(site) for site in SITES))
)


re_answer = re.compile(
    (
        r'^https?://({site})'
        r'/a/([0-9]+)'
        r'(?:/[0-9]*)?$'
    ).format(site='|'.join('(?:{0})'.format(site) for site in SITES))
)


class StackExchangeBase(Item):
    """A StackOverflow question or answer.
    """
    def __init__(self, site, id):
        self.site = site
        self.id = id

    def __eq__(self, other):
        return (
            self.TYPE == other.TYPE
            and self.site == other.site
            and self.id == other.id
        )

    def __hash__(self):
        return hash(
            (self.TYPE, self.site, self.id),
        )


class StackExchangeQuestion(StackExchangeBase):
    """A stackexchange question, that can be watched for new answers.
    """
    TYPE = 'StackExchange Question'

    @classmethod
    def is_url_reference(cls, url):
        m = re_question.match(url)
        return m is not None

    @classmethod
    def create(cls, url):
        m = re_question.match(url)
        if m is None:
            raise InvalidReference
        site, id = m.groups()
        id = int(id)
        return cls(site, id)

    def url(self):
        return 'https://{site}/q/{id}'.format(site=self.site, id=self.id)


class StackExchangeAnswer(StackExchangeBase):
    """A stackexchange answer, that can be watched for edits and comments.
    """
    TYPE = 'StackExchange Answer'

    @classmethod
    def is_url_reference(cls, url):
        m = re_answer.match(url)
        return m is not None

    @classmethod
    def create(cls, url):
        m = re_answer.match(url)
        if m is None:
            raise InvalidReference
        site, id = m.groups()
        id = int(id)
        return cls(site, id)

    def url(self):
        return 'https://{site}/a/{id}'.format(site=self.site, id=self.id)
