import asyncio
import logging
import re
import requests

from .base import Item, InvalidReference, batching
from .utils import batch


logger = logging.getLogger(__name__)


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


@batching.register
def batch_queries(queries):
    """Batches queries to StackOverflow.
    """
    BATCH_SIZE = 100

    logger.info("Sending %d batch queries", len(queries))

    # Organize queries by type and site
    organized_queries = {}
    for (type, site, id), future in queries:
        organized_queries.setdefault((type, site), []).append((id, future))

    # Loop on groups
    for (type, site), queries in organized_queries.items():
        # Loop over batches of size <= 100
        for queries in batch(queries, BATCH_SIZE):
            logger.info(
                "Sending batch of %d queries, type=%r site=%r",
                len(queries), type, site,
            )
            queries = dict(queries)
            if type == 'post':
                # Send query
                req = requests.get(
                    (
                        'https://api.stackexchange.com/2.3'
                        + '/posts/{ids}?site={site}'
                    ).format(
                        ids=';'.join('%d' % e for e in queries.keys()),
                        site=site,
                    )
                )
                req.raise_for_status()

                # Resolve futures for queries contained in this batch
                for post in req.json()['items']:
                    future = queries[post['post_id']]
                    future.set_result(post)
            elif type == 'comments':
                # Send query
                req = requests.get(
                    (
                        'https://api.stackexchange.com/2.3'
                        + '/posts/{ids}/comments?site={site}'
                    ).format(
                        ids=';'.join('%d' % e for e in queries.keys()),
                        site=site,
                    )
                )
                req.raise_for_status()

                # Organize comments by post
                posts = {id: [] for id in queries.keys()}
                for item in req.json()['items']:
                    posts[item['post_id']].append(item)

                # Resolve futures for queries contained in this batch
                for post_id, comments in posts.items():
                    future = queries[post_id]
                    future.set_result(comments)
            else:
                raise AssertionError


class StackExchangeBase(Item):
    """A StackOverflow question or answer.
    """
    def __init__(self, site, id):
        self.site = site
        self.id = id
        self.last_edit_date = None
        self.last_comment_date = None

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
    TYPE = 'stackexchange-question'

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

    def refresh(self):
        question = batch_queries(('post', self.site, self.id))
        comments = batch_queries(('comments', self.site, self.id))

        return asyncio.ensure_future(self._check(question, comments))

    async def _check(self, question, comments):
        changed = False

        # Check question edit date
        question = await question
        if question.get('last_edit_date') != self.last_edit_date:
            self.last_edit_date = question['last_edit_date']
            changed = True

        # Check last comment
        comments = await comments
        if comments:
            latest_comment = max(
                comment['creation_date']
                for comment in comments
            )
        else:
            latest_comment = None
        if (
            (self.last_comment_date is None and latest_comment is not None)
            or (
                self.last_comment_date is not None
                and latest_comment is not None
                and latest_comment > self.last_comment_date
            )
        ):
            changed = True
        self.last_comment_date = latest_comment

        return changed

    @classmethod
    def from_json(cls, obj):
        assert obj.keys() <= {
            'site', 'id', 'last_edit_date', 'last_comment_date',
        }
        item = cls(obj['site'], obj['id'])
        item.last_edit_date = obj.get('last_edit_date')
        item.last_comment_date = obj.get('last_comment_date')
        return item

    def to_json(self):
        return {
            'site': self.site,
            'id': self.id,
            'last_edit_date': self.last_edit_date,
            'last_comment_date': self.last_comment_date,
        }


class StackExchangeAnswer(StackExchangeBase):
    """A stackexchange answer, that can be watched for edits and comments.
    """
    TYPE = 'stackexchange-answer'

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

    def refresh(self):
        answer = batch_queries(('post', self.site, self.id))
        comments = batch_queries(('comments', self.site, self.id))

        return asyncio.create_task(self._check(answer, comments))

    async def _check(self, answer, comments):
        changed = False

        # Check question edit date
        answer = await answer
        if answer.get('last_edit_date') != self.last_edit_date:
            self.last_edit_date = answer['last_edit_date']
            changed = True

        # Check last comment
        comments = await comments
        if comments:
            latest_comment = max(
                comment['creation_date']
                for comment in comments
            )
        else:
            latest_comment = None
        if (
            (self.last_comment_date is None and latest_comment is not None)
            or (
                self.last_comment_date is not None
                and latest_comment is not None
                and latest_comment > self.last_comment_date
            )
        ):
            changed = True
        self.last_comment_date = latest_comment

        return changed

    @classmethod
    def from_json(cls, obj):
        assert obj.keys() <= {
            'site', 'id', 'last_edit_date', 'last_comment_date',
        }
        item = cls(obj['site'], obj['id'])
        item.last_edit_date = obj.get('last_edit_date')
        item.last_comment_date = obj.get('last_comment_date')
        return item

    def to_json(self):
        return {
            'site': self.site,
            'id': self.id,
            'last_edit_date': self.last_edit_date,
            'last_comment_date': self.last_comment_date,
        }
