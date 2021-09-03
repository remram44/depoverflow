import re

from .base import Item, InvalidReference


re_issue = re.compile(
    r'^https?://github\.com/([^/]+/[^/]+)/issues/([0-9]+)/?$'
)

re_pull_request = re.compile(
    r'^https?://github\.com/([^/]+/[^/]+)/pull/([0-9]+)/?$'
)


class GithubBase(Item):
    """A GitHub issue or pull request.
    """
    def __init__(self, repo, number):
        self.repo = repo
        self.number = number

    def __eq__(self, other):
        return (
            self.TYPE == other.TYPE
            and self.repo == other.repo
            and self.number == other.number
        )

    def __hash__(self):
        return hash(
            (self.TYPE, self.repo, self.number),
        )

    @classmethod
    def from_json(cls, obj):
        assert obj.keys() <= {'repo', 'number'}
        item = cls(obj['repo'], obj['number'])
        return item

    def to_json(self):
        return {
            'repo': self.repo,
            'number': self.number,
        }


class GithubIssue(GithubBase):
    """A GitHub issue, that can be watched for comments and status changes.
    """
    TYPE = 'github-issue'

    @classmethod
    def is_url_reference(cls, url):
        m = re_issue.match(url)
        return m is not None

    @classmethod
    def create(cls, url):
        m = re_issue.match(url)
        if m is None:
            raise InvalidReference
        repo, number = m.groups()
        number = int(number)
        return cls(repo, number)

    def url(self):
        return 'https://github.com/{repo}/issues/{number}'.format(
            repo=self.repo,
            number=self.number,
        )


class GithubPullRequest(GithubBase):
    """A GitHub PR, that can be watched for comments and status changes.
    """
    TYPE = 'github-pr'

    @classmethod
    def is_url_reference(cls, url):
        m = re_pull_request.match(url)
        return m is not None

    @classmethod
    def create(cls, url):
        m = re_pull_request.match(url)
        if m is None:
            raise InvalidReference
        repo, number = m.groups()
        number = int(number)
        return cls(repo, number)

    def url(self):
        return 'https://github.com/{repo}/pull/{number}'.format(
            repo=self.repo,
            number=self.number,
        )
